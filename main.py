import cmd
import json
import argparse
import stat
import pwd
import grp
from datetime import datetime

from ext3_fs import Ext3FileSystem


class FileSystemCLI(cmd.Cmd):
    # intro = r"""ext3plorer"""
    prompt = '(ext3plorer)-> '

    def __init__(self, image_path, inode):
        super().__init__()
        self.image_path = image_path
        self.inode = inode
        self.fs = Ext3FileSystem(image_path=image_path, inode=inode)

    def do_print(self, args):
        """Команда print: вывод информации о файловой системе"""
        parser = argparse.ArgumentParser(prog='print')
        parser.add_argument('--type', choices=['sb', 'gd', 'inode', 'xattr', 'all'], help='Тип информации для вывода')

        try:
            args = parser.parse_args(args.split())
            if args.type == 'sb':
                print('---> Данные суперблока <---')
                print(json.dumps(self.fs.sb_info, indent=4))
            elif args.type == 'gd':
                print('---> Данные дескриптора группы <---')
                print(json.dumps(self.fs.get_gd_info(), indent=4))
            elif args.type == 'inode':
                print('---> Информация об inode <---')

                a = self.fs.get_inode_info()

                a['i_mode'] = [a['i_mode'], oct(a['i_mode']), stat.filemode(a['i_mode'])]

                a['i_atime'] = [a['i_atime'], datetime.fromtimestamp(a['i_atime']).strftime('%Y-%m-%d %H:%M:%S')]
                a['i_ctime'] = [a['i_ctime'], datetime.fromtimestamp(a['i_ctime']).strftime('%Y-%m-%d %H:%M:%S')]
                a['i_mtime'] = [a['i_mtime'], datetime.fromtimestamp(a['i_mtime']).strftime('%Y-%m-%d %H:%M:%S')]
                try:
                    a['i_uid'] = [a['i_uid'], pwd.getpwuid(a['i_uid']).pw_name]
                except KeyError:
                    a['i_uid'] = [a['i_uid'], 'NOT_FOUND']

                try:
                    a['i_gid'] = [a['i_gid'], grp.getgrgid(a['i_gid']).gr_name]
                except KeyError:
                    a['i_gid'] = [a['i_gid'], 'NOT_FOUND']

                print(json.dumps(a, indent=4))
            elif args.type == 'xattr':
                print('---> Расширенные атрибуты <---')
                b = self.fs.get_acl_info()
                print(json.dumps(b, ensure_ascii=False, indent=4))

            elif args.type == 'all':
                print('---> Данные суперблока <---')
                print(json.dumps(self.fs.sb_info, indent=4))
                print('---> Данные дескриптора группы <---')
                print(json.dumps(self.fs.get_gd_info(), indent=4))
                print('---> Информация об inode <---')
                a = self.fs.get_inode_info()

                a['i_mode'] = [a['i_mode'], oct(a['i_mode']), stat.filemode(a['i_mode'])]
                a['i_atime'] = [a['i_atime'], datetime.fromtimestamp(a['i_atime']).strftime('%Y-%m-%d %H:%M:%S')]
                a['i_ctime'] = [a['i_ctime'], datetime.fromtimestamp(a['i_ctime']).strftime('%Y-%m-%d %H:%M:%S')]
                a['i_mtime'] = [a['i_mtime'], datetime.fromtimestamp(a['i_mtime']).strftime('%Y-%m-%d %H:%M:%S')]
                try:
                    a['i_uid'] = [a['i_uid'], pwd.getpwuid(a['i_uid']).pw_name]
                except KeyError:
                    a['i_uid'] = [a['i_uid'], 'NOT_FOUND']
                try:
                    a['i_gid'] = [a['i_gid'], grp.getgrgid(a['i_gid']).gr_name]
                except KeyError:
                    a['i_gid'] = [a['i_gid'], 'NOT_FOUND']
                print(json.dumps(a, indent=4))

                print('---> Расширенные атрибуты <---')
                b = self.fs.get_acl_info()
                print(json.dumps(b, ensure_ascii=False, indent=4))
        except SystemExit:
            print("Ошибка: не верные аргументы для команды print")

    def do_modify_inode(self, args):
        """Команда modify: изменение метаданных файлов по inode"""
        parser = argparse.ArgumentParser(prog='modify')
        parser.add_argument('--field', help='Поле для изменения (например, uid, gid, i_mode)')
        parser.add_argument('--value', help='Новое значение для поля')

        try:
            args = parser.parse_args(args.split())
            if args.field and args.value:
                self.fs.modify_inode_field(args.field, int(args.value))
            else:
                print("Необходимо указать и поле, и значение")
        except SystemExit:
            print("Ошибка: не верные аргументы для команды modify_inode")

    def do_exit(self, arg):
        """Выход из программы"""
        print("Выход из программы.")
        return True


def main():
    parser = argparse.ArgumentParser(description='Запуск интерактивной программы для работы с inode')
    parser.add_argument('image_path', help='Путь до файла образа ФС')
    parser.add_argument('inode', type=int, help='Номер inode')
    args = parser.parse_args()

    cli = FileSystemCLI(image_path=args.image_path, inode=args.inode)
    cli.cmdloop()


if __name__ == "__main__":
    main()

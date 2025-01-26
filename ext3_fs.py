import ext3_structure


class Ext3FileSystem:
    def __init__(self, image_path, inode):
        self.image_path = image_path
        self.inode_number = inode

        self.sb_info = self.read_superblock()

        self.block_size = 1024 * pow(2, self.sb_info['s_log_block_size'])
        self.block_group = (self.inode_number - 1) // self.sb_info['s_inodes_per_group']  # группа блоков в которой находится inode

    def read_superblock(self):
        sb_offset, sb_size = 1024, 1024
        sb_raw_info = self.read_data(sb_offset, sb_size)
        return self.parse_data(sb_raw_info, ext3_structure.super_block)

    def read_data(self, offset, size):
        with open(self.image_path, 'rb') as rfile:
            rfile.seek(offset)
            return rfile.read(size)

    def parse_data(self, data, collection, value_format='dec'):
        result = {}
        for name, info in collection.items():
            offset, size, byteorder = info['offset'], info['size'], info['byteorder']
            field_value = int.from_bytes(data[offset:offset + size], byteorder=byteorder)
            if value_format == 'hex':
                field_value = hex(field_value)
            result[name] = field_value
        return result

    def get_gd_info(self):
        gd_offset = 2048 + self.block_group * 32
        gd_raw_info = self.read_data(gd_offset, 32)
        return self.parse_data(gd_raw_info, ext3_structure.group_desc)

    def get_inode_info(self):
        gd_info = self.get_gd_info()
        inode_table_offset = gd_info['bg_inode_table_lo'] * self.block_size
        inode_offset = inode_table_offset + (self.inode_number - 1) * self.sb_info['s_inode_size']
        inode_raw_info = self.read_data(inode_offset, self.sb_info['s_inode_size'])
        return self.parse_data(inode_raw_info, ext3_structure.inode)

    def get_i_block_data(self):
        i_block_offset = self.get_inode_info()['i_block[15]'] * self.block_size  # указатель на блок данных
        i_block_raw_info = self.read_data(i_block_offset, self.get_inode_info()['i_size'])
        return i_block_raw_info

    def get_acl_info(self):
        acl_offset = self.get_inode_info()['i_file_acl'] * self.block_size
        acl_raw_info = self.read_data(acl_offset, self.block_size)

        if self.is_zero_filled(acl_raw_info, 0, self.block_size):
            print("Нет расширенных атрибутов")
            return None

        acl_json_info = {
            'offset': acl_offset,
            'ext4_xattr_header': self.parse_data(acl_raw_info, collection=ext3_structure.file_acl['ext4_xattr_header'],
                                                 value_format='hex'),
            'ext4_xattr_entries': []
        }

        # Смещение начала первого ext4_xattr_entry сразу после заголовка
        entry_offset = 32  # Размер ext4_xattr_header, см. ext3_structure.py

        while entry_offset < self.block_size:
            # Чтение текущего ext4_xattr_entry
            entry = self.parse_data(acl_raw_info[entry_offset:], collection=ext3_structure.file_acl['ext4_xattr_entry'],
                                    value_format='hex')

            e_name_len = int(entry['e_name_len'], 16)
            if e_name_len == 0:  # Конец списка атрибутов
                break

            # Извлечение имени атрибута
            e_name_offset = entry_offset + ext3_structure.file_acl['ext4_xattr_entry']['e_hash']['offset'] + 4
            e_name = acl_raw_info[e_name_offset:e_name_offset + e_name_len].decode('utf-8')

            # Извлечение значения атрибута
            e_value_offset = int(entry['e_value_offs'], 16)
            e_value_size = int(entry['e_value_size'], 16)
            e_value_data = acl_raw_info[e_value_offset:e_value_offset + e_value_size]

            entry_data = {
                'e_name': e_name,
                'e_value_data': e_value_data.hex(),  # Конвертируем в hex для удобства
                'e_raw_entry': entry
            }

            acl_json_info['ext4_xattr_entries'].append(entry_data)

            # Переход к следующему атрибуту (минимум 16 байт на атрибут)
            entry_offset += max(16, e_name_len + 16)

        return acl_json_info

    def is_zero_filled(self, data, offset, size):
        # True, если все байты в диапазоне равны 0x0, иначе False
        return all(byte == 0x0 for byte in data[offset:offset + size])

    def print_data(self, offset=0, count=64, offset_format='dec', ascii_field=True):
        data = self.read_data(offset, count)
        print(f'\nФайл: {self.image_path}')
        print('Offset    00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F')
        print('---------------------------------------------------------')
        for i in range(0, len(data), 16):
            chunk = data[i:i + 16]
            address = offset + i
            if offset_format == 'hex':
                address_str = f'{address:08X}'
            else:
                address_str = f'{address:08}'
            hex_bytes = ' '.join(f'{byte:02X}' for byte in chunk)
            hex_bytes = hex_bytes.ljust(47)
            if ascii_field:
                ascii_part = ''.join(chr(byte) if 32 <= byte <= 126 else '.' for byte in chunk)
                print(f"{address_str}  {hex_bytes}   {ascii_part}")
            else:
                print(f'{address_str}  {hex_bytes}')

    def write_data(self, output_path, data, offset=0):
        # Записывает байт-строку в файл с указанного смещения
        with open(output_path, 'r+b') as wfile:  # Открываем файл в режиме записи
            wfile.seek(offset)
            wfile.write(data)
        print(f"Данные записаны в файл: {output_path} со смещением {offset}")

    def change_data(self, data, offset, new_value, size):
        # Изменяет данные, заменяя значение с указанного смещения
        new_data = data[:offset] + new_value[:size] + data[offset + size:]
        return new_data

    def modify_inode_field(self, field_name, new_value):
        inode_info = self.get_inode_info()
        inode_table_offset = self.get_gd_info()['bg_inode_table_lo'] * self.block_size
        inode_offset = inode_table_offset + (self.inode_number - 1) * self.sb_info['s_inode_size']

        if field_name in inode_info:
            print(f"Изменение поля {field_name} с {inode_info[field_name]} на {new_value}")
            # Преобразуем новое значение в байты
            new_value_bytes = int.to_bytes(new_value, length=ext3_structure.inode[field_name]['size'], byteorder=ext3_structure.inode[field_name]['byteorder'])
            field_offset = ext3_structure.inode[field_name]['offset']
            inode_raw = self.read_data(inode_offset, self.sb_info['s_inode_size'])
            modified_inode = self.change_data(inode_raw, field_offset, new_value_bytes, ext3_structure.inode[field_name]['size'])

            # Записываем измененные данные
            self.write_data(self.image_path, modified_inode, inode_offset)
        else:
            print(f"Поле {field_name} не найдено")


def main():
    pass


if __name__ == "__main__":
    main()
    

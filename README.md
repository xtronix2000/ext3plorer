# ex3plorer

## Описание проекта

Этот проект предоставляет возможность для работы с образами файловых систем на основе ext3, позволяя изменять атрибуты файлов на низком уровне, включая такие поля inode, как права доступа, а также извлекать информацию о inode. 

## Структура проекта

- **ext3_structure.py**: Содержит описание структуры ФС ext3.
- **ext3_fs.py**: Содержит классы и функции для для манипуляции с файловой системой.
- **main.py**: Основной исполняемый файл программы.

## Запуск программы 

```bash
python3 main.py IMAGE_PATH INODE
```
Например:
```bash
python3 main.py image.img 12
python3 main.py /dev/sda1 777
```
Дальнейшее управление программой выплоняется с помощью команд

## Вывод информации на о выбранной структуре командой `print`

Возможные значения `--type`: 
- sb - данные о суперблоке,
- gd - данные дескриптора группы
- inode - информация об inode
- xattr - расширенные атрибутацииы (пока только 1)
- all - вывод всей информации

```bash
(ex3plorer)-> print --type inode
```
## Изменение полей inode

```bash
(ex3plorer)-> modify_inode --field FILED_NAME --value VALUE
```
Например:
```bash
(ex3plorer)-> modify_inode --field i_uid --value 1002

(ex3plorer)-> modify_inode --field i_mode --value 35236
```
Значения ключа `--field` совпадает с ключами структуры inode при выводе командой `print` и позвоняет изменить любое поле inode. Но я бы не рекомендовал изменять ничего кроме i_mode, i_uid, i_gid, i_atime, i_ctime, i_mtime во избеждание ошибок.

Значения ключа`--value` заносятся в виде целого десятичного числа, т.е права i_mode имеют представление drwxr-xr-x --> 40755 --> 16877, вскоре я это исправлю

При изменении полей inode командой `modify`, изменения автоматически записываются в переданный на вход программы файл образа. Рекомендуется сделать копию и работать с ней во избежание ошибок

## Доп. материал

1. О структуре суперблока и дескрипторов групп [тут](https://www.kernel.org/doc/html/latest/filesystems/ext4/globals.html)
2. О структуре inode и немного про расширенные атрибуты [тут](https://www.kernel.org/doc/html/latest/filesystems/ext4/dynamic.html)
3. Расширенные атрибуты ext3 [тут](https://studfile.net/preview/8326012/page:5/)

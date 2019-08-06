import json
import glob
from PIL import Image, ExifTags
import base64
import os


def resize_rect(src_dir, dst_dir, *cut_rect_sizes):
    cut_rect_sizes = list(cut_rect_sizes)
    if len(cut_rect_sizes) == 0:
        cut_rect_sizes.append(300)
    cut_rect_sizes.sort()

    json_path_list = glob.glob(src_dir + '/*.json')
    for path in json_path_list:
        if not os.path.exists(path.replace('json', 'jpg')):
            json_path_list.remove(path)

    for json_count, path in enumerate(json_path_list):
        print(f'第{json_count + 1}个json文件:{path}')
        with open(path) as f:
            data = json.load(f)

            org_img_height = data['imageHeight']
            org_img_width = data['imageWidth']
            org_img_size_min = min(org_img_height, org_img_width)

            print(f'原图:{org_img_width}*{org_img_height}')

            shapes = data['shapes']
            shape_num = len(shapes)
            suc_num = 0
            for shape_count, shape in enumerate(shapes):
                print(f'第{shape_count + 1}个矩形框')
                point1_x, point1_y = (
                    round(shape['points'][0][0]), round(shape['points'][0][1]))
                point2_x, point2_y = (
                    round(shape['points'][1][0]), round(shape['points'][1][1]))

                x_min, x_max = (point1_x, point2_x) if point1_x < point2_x else (
                    point2_x, point1_x)
                y_min, y_max = (point1_y, point2_y) if point1_y < point2_y else (
                    point2_y, point1_y)

                print(f'初始左上点:（{x_min},{y_min}）,右下点:({x_max},{y_max})')

                org_rect_width = x_max - x_min
                org_rect_height = y_max - y_min

                print(f'初始矩形框大小:{org_rect_width}*{org_rect_height}')

                org_rect_size = max(org_rect_width, org_rect_height)

                is_super_size = False

                for size in cut_rect_sizes:
                    if org_rect_size <= size:
                        cut_rect_size = size
                        break
                else:
                    to_left_dis = x_min
                    to_right_dis = org_img_width - x_max
                    to_top_dis = y_min
                    to_bottom_dis = org_img_height - y_max
                    dis = min(max(to_left_dis, to_right_dis), max(to_top_dis, to_bottom_dis))
                    if dis > 150:
                        dis = 150
                    cut_rect_size = org_rect_size + dis
                    is_super_size = True

                print(f'裁剪尺寸{cut_rect_size}')

                # 超出图像范围
                # if cut_rect_size > org_img_size_min:
                #     print('超出图像范围')
                #     error_num += 1
                #     shutil.copy(path, error_dir)
                #     shutil.copy(path.replace('json', 'jpg'), error_dir)

                # else:
                suc_num += 1
                print(f'裁剪矩形框大小:{cut_rect_size}*{cut_rect_size}')

                # print(f'点一:({point1_x},{point1_y}),点二:({point2_x},{point2_y})')

                # point_left_top=(x_min,y_min)
                # point_right_bottom=(x_max,y_max)

                point_center_x, point_center_y = (
                    round((x_min + x_max) / 2), round((y_min + y_max) / 2))

                print(f'中心点:({point_center_x},{point_center_y})')

                half_size = round(cut_rect_size / 2)

                x_min_cut = point_center_x - half_size
                x_max_cut = point_center_x + half_size
                y_min_cut = point_center_y - half_size
                y_max_cut = point_center_y + half_size

                if x_min_cut < 0:
                    x_max_cut += abs(x_min_cut)
                    x_min_cut = 0

                if x_max_cut > org_img_width:
                    x_min_cut -= x_max_cut - org_img_width
                    x_max_cut = org_img_width

                if y_min_cut < 0:
                    y_max_cut += abs(y_min_cut)
                    y_min_cut = 0

                if y_max_cut > org_img_height:
                    y_min_cut -= y_max_cut - org_img_height
                    y_max_cut = org_img_height

                print(
                    f'裁剪左上点:({x_min_cut},{y_min_cut}),右下点:({x_max_cut},{y_max_cut})')

                img = Image.open(path.replace('json', 'jpg'))

                try:
                    for orientation in ExifTags.TAGS.keys():
                        if ExifTags.TAGS[orientation] == 'Orientation': break
                    exif = dict(img._getexif().items())
                    if exif[orientation] == 3:
                        img = img.rotate(180, expand=True)
                    elif exif[orientation] == 6:
                        img = img.rotate(270, expand=True)
                    elif exif[orientation] == 8:
                        img = img.rotate(90, expand=True)
                except:
                    # print('\033[31mERROR\033[0m')
                    pass

                img1 = img.crop((x_min_cut, y_min_cut, x_max_cut, y_max_cut))

                x_min_in_cut_img = x_min - x_min_cut
                x_max_in_cut_img = x_min_in_cut_img + org_rect_width
                y_min_in_cut_img = y_min - y_min_cut
                y_max_in_cut_img = y_min_in_cut_img + org_rect_height

                data['imageWidth'] = cut_rect_size
                data['imageHeight'] = cut_rect_size

                if cut_rect_size > org_img_size_min:
                    x = y = 0
                    if org_img_width < cut_rect_size:
                        x_min_cut = 0
                        x_max_cut = org_img_width
                        x = round((cut_rect_size - org_img_width) / 2)
                    if org_img_height < cut_rect_size:
                        y_min_cut = 0
                        y_max_cut = org_img_height
                        y = round((cut_rect_size - org_img_height) / 2)

                    img2 = img.crop((x_min_cut, y_min_cut, x_max_cut, y_max_cut))
                    img1 = Image.new('RGB', (cut_rect_size, cut_rect_size), (255, 255, 255))

                    img1.paste(img2, (x, y, x + (x_max_cut - x_min_cut), y + (y_max_cut - y_min_cut)))
                    x_min_in_cut_img = x_min - x_min_cut + x
                    x_max_in_cut_img = x_min_in_cut_img + (org_rect_width)
                    y_min_in_cut_img = y_min - y_min_cut + y
                    y_max_in_cut_img = y_min_in_cut_img + (org_rect_height)

                if is_super_size:
                    img1 = img1.resize((cut_rect_sizes[-1], cut_rect_sizes[-1]))

                    rate = cut_rect_sizes[-1] / cut_rect_size
                    x_min_in_cut_img = round(x_min_in_cut_img * rate)
                    x_max_in_cut_img = round(x_max_in_cut_img * rate)
                    y_min_in_cut_img = round(y_min_in_cut_img * rate)
                    y_max_in_cut_img = round(y_max_in_cut_img * rate)

                    data['imageWidth'] = cut_rect_sizes[-1]
                    data['imageHeight'] = cut_rect_sizes[-1]

                img_name = data['imagePath'].replace('.jpg', '').replace('.JPG', '')
                img_dst_path = dst_dir + '/' + img_name + '_' + str(suc_num) + '.jpg'
                img1.save(img_dst_path)

                with open(img_dst_path, 'rb') as f:
                    base64_data = base64.b64encode(
                        f.read()).decode('utf-8')

                data['imageData'] = base64_data

                shape['points'] = [[x_min_in_cut_img, y_min_in_cut_img],
                                   [x_max_in_cut_img, y_max_in_cut_img]]
                data['shapes'] = [shape]

                with open(img_dst_path.replace('jpg', 'json'), 'w') as f:
                    json.dump(data, f, indent=4)
                print(f'成功裁剪第{shape_count + 1}个矩形',
                      end='\n**************************************************************\n')
        print(f'第{json_count + 1}个文件，共:{shape_num}成功:{suc_num}',
              end='\n------------------------------------------------------------------------------------------\n')


def main():
    src_dir = glob.glob(r'F:\Lym\图片\*')
    dst_dir = []
    for d in src_dir:
        path = r'C:\Users\Administrator\Desktop\2019.8.6' + '\\' + d.split('\\')[-1]
        dst_dir.append(path)
        os.mkdir(path)
    # src_dir = 'C:/Users/Administrator/Desktop/error'
    # dst_dir = 'C:/Users/Administrator/Desktop/dst'
    # error_dir = 'C:/Users/Administrator/Desktop/er'
    for src, dst in zip(src_dir, dst_dir):
        resize_rect(src, dst, 300, 500, 800)


if __name__ == '__main__':
    main()

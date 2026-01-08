import time
import re
import os
audio_offset_pattern = r"AudioOffset:(-?\d+)"
timing_pattern = r"timing\((-?\d+),([\d.]+),([\d.]+)\);"
tap_pattern = r"\((-?\d+),(\d+)\);"
hold_pattern = r"hold\((-?\d+),(-?\d+),(\d+)\);"
arc_pattern = r"arc\((-?\d+),(-?\d+),(-?[\d.]+),(-?[\d.]+),(\w+),(-?[\d.]+),(-?[\d.]+),(\d+),(\w+),(\w+)\)(?:\[(.*)\])?;"
scenecontrol_pattern = r"scenecontrol\((-?\d+),(\w+),([\d.]+),(\d+)\);"
empty_timinggroup_pattern = r"timinggroup(?:\(noinput\)|\(\))\{\n\}"
instructions_0 = """
欢迎使用铺面处理脚本！此脚本主要用于提取铺面特定段落或调整铺面音频延迟AudioOffset。
脚本作者：CE2Y   github地址：http://github.com/0ce2y0
"""
instructions_1 = """
说明：若需提取铺面的特定段落，请输入数字1；
若需在保证音频与铺面完全对准同时将铺面AudioOffset音频延迟调整为0，请输入数字2。
"""
instructions_2 = """
分别输入铺面片段起始位置时间与结束位置时间，铺面片段起始与结束时间可从Arcade中查取。
"""
instructions_3 = """
请输入所需调整的延迟时间。
示例：Arcade中显示音频延迟为100，则输入数字100。
"""

# =========================================================

def check_file_path(input_path):
# 检验文件路径与格式是否正确
    try:
        with open(input_path, 'r', encoding='utf-8') as file:
            content = file.read()
            if "AudioOffset:" not in content and "timing(0," not in content and "-" not in content:
                raise ValueError(f"文件格式错误，请确保文件为正确的铺面文件。")
            else:
                return True
    except UnicodeDecodeError:
        print(f"文件编码错误，请确保文件为UTF-8编码。")  
    except FileNotFoundError:
        print(f"文件未找到，请检查路径是否正确。")
    except PermissionError:
        print(f"没有权限访问该文件，请检查权限设置。")
    except ValueError as ve:
        print(ve)
    except Exception as e:
        print(f"发生未知错误：{e}")

# =========================================================

def extract_file(input_number_one, input_number_two): 
# 提取铺面片段并移至开头
    try:
        length = int(input_number_two) - int(input_number_one)

        def subtract_timing(match):
            new_match_group_1 = int(match.group(1)) - int(input_number_one)
            return f"timing({new_match_group_1},{match.group(2)},{match.group(3)});"

        def subtract_tap(match):
            new_match_group_1 = int(match.group(1)) - int(input_number_one)
            return f"({new_match_group_1},{match.group(2)});"

        def subtract_hold(match):
            new_match_group_1 = int(match.group(1)) - int(input_number_one)
            new_match_group_2 = int(match.group(2)) - int(input_number_one)
            return f"hold({new_match_group_1},{new_match_group_2},{match.group(3)});"

        def subtract_arc(match):
            new_match_group_1 = int(match.group(1)) - int(input_number_one)
            new_match_group_2 = int(match.group(2)) - int(input_number_one)
            # 单独处理arc部分
            new_base_arc = f"arc({new_match_group_1},{new_match_group_2},{match.group(3)},{match.group(4)},{match.group(5)},{match.group(6)},{match.group(7)},{match.group(8)},{match.group(9)},{match.group(10)})"
            # 单独处理arctap部分
            new_arctap = match.group(11)
            if new_arctap:
                arctap_matches = re.findall(r"arctap\((-?\d+)\)", new_arctap)
                if arctap_matches:
                    adjusted_arctaps = []
                    for arctap_time in arctap_matches:
                        adjusted_time = int(arctap_time) - int(input_number_one)
                        adjusted_arctaps.append(f"arctap({adjusted_time})")
                    return new_base_arc + "[" + ",".join(adjusted_arctaps) + "]" + ";"
            return new_base_arc + ";"

        def subtract_scenecontrol(match):
            new_match_group_1 = int(match.group(1)) - int(input_number_one)
            return f"scenecontrol({new_match_group_1},{match.group(2)},{match.group(3)},{match.group(4)});"

        def delete_timing(match):
            if int(match.group(1)) >= int(length):
                return ""
            else:
                return f"timing({match.group(1)},{match.group(2)},{match.group(3)});"

        def delete_tap(match):
            if int(match.group(1)) < 0 or int(match.group(1)) >= int(length):
                return ""
            else:
                return f"({match.group(1)},{match.group(2)});"
        
        def delete_hold(match):
            if int(match.group(1)) < 0 and int(match.group(2)) < 0:
                return ""
            elif int(match.group(1)) >= int(length) and int(match.group(2)) >= int(length):
                return ""
            elif int(match.group(1)) < 0 and int(match.group(2)) > 0:
                return f"hold(0,{match.group(2)},{match.group(3)});"
            elif int(match.group(1)) < int(length) and int(match.group(2)) >= int(length):
                return f"hold({match.group(1)},{int(length)},{match.group(3)});"
            else:
                return f"hold({match.group(1)},{match.group(2)},{match.group(3)});"
        
        def delete_arc(match):
            # 单独处理arc部分
            if int(match.group(1)) < 0 and int(match.group(2)) <= 0:
                base_arc = ""
            elif int(match.group(1)) < 0 and 0 < int(match.group(2)) <= length:
                base_arc = f"arc(0,{match.group(2)},{match.group(3)},{match.group(4)},{match.group(5)},{match.group(6)},{match.group(7)},{match.group(8)},{match.group(9)},{match.group(10)})"
            elif int(match.group(1)) < 0 and int(match.group(2)) > length:
                base_arc = f"arc(0,{length},{match.group(3)},{match.group(4)},{match.group(5)},{match.group(6)},{match.group(7)},{match.group(8)},{match.group(9)},{match.group(10)})"
            elif 0 <= int(match.group(1)) < length and 0 < int(match.group(2)) <= length:
                base_arc = f"arc({match.group(1)},{match.group(2)},{match.group(3)},{match.group(4)},{match.group(5)},{match.group(6)},{match.group(7)},{match.group(8)},{match.group(9)},{match.group(10)})"
            elif 0 <= int(match.group(1)) < length and int(match.group(2)) > length:
                base_arc = f"arc({match.group(1)},{length},{match.group(3)},{match.group(4)},{match.group(5)},{match.group(6)},{match.group(7)},{match.group(8)},{match.group(9)},{match.group(10)})"
            elif int(match.group(1)) >= length:
                base_arc = ""
            # 单独处理arctap部分并返回结果
            arctap = match.group(11)
            if arctap:
                arctap_matches = re.findall(r"arctap\((-?\d+)\)", arctap)
                arctap_group = []
                for single_arctap in arctap_matches:
                    if 0 <= int(single_arctap) <= length:
                        arctap_group.append(f"arctap({single_arctap})")
                if arctap_group:
                    return base_arc + "[" + ",".join(arctap_group) + "]" + ";"
            return base_arc + ";"
        
        def delete_scenecontrol(match):
            if int(match.group(1)) < 0 or int(match.group(1)) >= int(length):
                return ""
            else:
                return f"scenecontrol({match.group(1)},{match.group(2)},{match.group(3)},{match.group(4)});"
       
        # 处理流程
        with open(input_path, 'r', encoding='utf-8') as file:
            lines = file.read()
            # 对铺面元素进行移动处理
            lines = re.sub(timing_pattern, subtract_timing, lines)
            lines = re.sub(tap_pattern, subtract_tap, lines)
            lines = re.sub(hold_pattern, subtract_hold, lines)
            lines = re.sub(arc_pattern, subtract_arc, lines)
            lines = re.sub(scenecontrol_pattern, subtract_scenecontrol, lines)
            # 删除范围外的铺面元素
            lines = re.sub(timing_pattern, delete_timing, lines)
            lines = re.sub(tap_pattern, delete_tap, lines)
            lines = re.sub(hold_pattern, delete_hold, lines)
            lines = re.sub(arc_pattern, delete_arc, lines)
            lines = re.sub(scenecontrol_pattern, delete_scenecontrol, lines)
            # 清理多余元素
            lines = re.sub(r'^\s*;\s*$', '', lines, flags=re.MULTILINE)
            lines = re.sub(r'^  \n', '\n', lines, flags=re.MULTILINE)
            lines = re.sub(r'\n+', '\n', lines)
            lines = re.sub(empty_timinggroup_pattern, '\n', lines)
            lines = re.sub(r'^\s*;\s*$', '', lines, flags=re.MULTILINE)
            lines = re.sub(r'\n+', '\n', lines)
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(lines)

    except Exception as e:
        print(f"执行失败：出现错误：{str(e)}")

# =========================================================

def audio_delay_processing(input_audio_delay):
# 音频延迟对准
    try:
        def adjust_audiooffset(match):
            new_match_audiooffset = int(match.group(1)) + int(input_audio_delay)
            return f"AudioOffset: {new_match_audiooffset}"

        def adjust_timing(match):
            new_match_group_1 = int(match.group(1)) + int(input_audio_delay)
            return f"timing({new_match_group_1},{match.group(2)},{match.group(3)});"
        
        def adjust_tap(match):
            new_match_group_1 = int(match.group(1)) + int(input_audio_delay)
            return f"({new_match_group_1},{match.group(2)});"

        def adjust_hold(match):
            new_match_group_1 = int(match.group(1)) + int(input_audio_delay)
            new_match_group_2 = int(match.group(2)) + int(input_audio_delay)
            return f"hold({new_match_group_1},{new_match_group_2},{match.group(3)});"
        
        def adjust_arc(match):
            new_match_group_1 = int(match.group(1)) + int(input_audio_delay)
            new_match_group_2 = int(match.group(2)) + int(input_audio_delay)
            # 单独处理arc部分
            new_base_arc = f"arc({new_match_group_1},{new_match_group_2},{match.group(3)},{match.group(4)},{match.group(5)},{match.group(6)},{match.group(7)},{match.group(8)},{match.group(9)},{match.group(10)})"
            # 单独处理arctap部分
            new_arctap = match.group(11)
            if new_arctap:
                arctap_matches = re.findall(r"arctap\((-?\d+)\)", new_arctap)
                if arctap_matches:
                    adjusted_arctaps = []
                    for arctap_time in arctap_matches:
                        adjusted_time = int(arctap_time) + int(input_audio_delay)
                        adjusted_arctaps.append(f"arctap({adjusted_time})")
                    return new_base_arc + "[" + ",".join(adjusted_arctaps) + "]" + ";"
            return new_base_arc + ";"

        def adjust_scenecontrol(match):
            new_match_group_1 = int(match.group(1)) + int(input_audio_delay)
            return f"scenecontrol({new_match_group_1},{match.group(2)},{match.group(3)},{match.group(4)});"

        # 处理流程
        with open(input_path, 'r', encoding='utf-8') as file:
            lines = file.read()
            # 对铺面元素进行移动处理
            lines = re.sub(audio_offset_pattern, adjust_audiooffset, lines)
            lines = re.sub(timing_pattern, adjust_timing, lines)
            lines = re.sub(tap_pattern, adjust_tap, lines)
            lines = re.sub(hold_pattern, adjust_hold, lines)
            lines = re.sub(arc_pattern, adjust_arc, lines)
            lines = re.sub(scenecontrol_pattern, adjust_scenecontrol, lines)
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(lines)

    except Exception as e:
        print(f"执行失败：出现错误：{str(e)}")

# =====================================================

# 主程序
if __name__ == "__main__":
    print(instructions_0)
    time.sleep(1)
    input_path = input("请复制铺面文件地址并粘贴于此处：")
    input_path = input_path.strip('"').strip("'")
    input_path = os.path.normpath(input_path)
    if check_file_path(input_path):
        file_dir = os.path.dirname(input_path)
        filename = os.path.basename(input_path)
        file_base, file_ext = os.path.splitext(filename)
        new_filename = f"{file_base}_new{file_ext}"
        output_path = os.path.join(file_dir, new_filename)
        print("铺面文件检查通过，开始处理铺面文件")
        time.sleep(1)
        print(instructions_1)
        while True:
            input_select = input("请选择需要执行的程序: ")
            if input_select == '1':
                print(instructions_2)
                time.sleep(0.5)
                while True:
                    input_number_one = input("请输入铺面片段起始时间：")
                    input_number_two = input("请输入铺面片段结束时间：")
                    if input_number_one.isdigit() and input_number_two.isdigit() and int(input_number_one) < int(input_number_two):
                        print("开始提取铺面片段并移动到起点位置......")
                        extract_file(input_number_one, input_number_two)
                        print("程序1运行结束！")
                        print("Tips: 起始时间为负数的Timing太难处理，脚本用完需要用Arcade/文本编辑器把多余的Timing删掉，不过不删也不影响铺面")
                        # 起始时间为负数的Timing太难特殊处理了，经第一部分运算后，会出现若干起始时间≤0的Timing，如果直接删除这些Timing会导致谱面文件开头没有timing从而导致铺面出错，所以只能选出最后一个起始时间≤0的Timing，并把起始时间改为0然后保留下来。然而这又涉及到timinggroup的情况，每个timinggroup内都有可能出现起始时间≤0的Timing，如果对timinggroup外和每个timinggroup内的Timing分别处理，这样写下来代码会非常长。所以我不想写了 ⌓‿⌓
                        break
                    else:
                        print("输入有误，请重新输入正确选项")
                break
            elif input_select == '2':
                print(instructions_3)
                time.sleep(0.5)
                while True:
                    input_audio_delay = input("请输入延迟时间：")
                    if int(input_audio_delay):
                        print("开始调整音频延迟......")
                        audio_delay_processing(input_audio_delay)
                        print("程序2运行结束！")
                        break
                    else:
                        print("输入有误，请重新输入正确选项")
                break
            else:
                print("输入有误，请重新输入正确选项")
    else:
        print("铺面文件检查未通过，程序终止")
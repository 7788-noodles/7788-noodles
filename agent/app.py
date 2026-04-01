from tools.command_parser import process_command


def print_welcome():
    print("==============================")
    print("智能生活助手（自然语言命令版）")
    print("==============================")
    print("你现在可以直接输入一句命令，不用再选菜单。")
    print("输入 帮助 查看支持的命令格式。")
    print("输入 exit 或 退出 结束程序。")
    print("==============================")


def main():
    print_welcome()

    while True:
        command = input("\n请输入命令：").strip()

        if command in ["exit", "退出"]:
            print("程序已退出。")
            break

        if not command:
            print("请输入有效命令。")
            continue

        try:
            result = process_command(command)
            print("\n" + result)
        except ValueError as e:
            print(f"\n出错了: {e}")
        except Exception as e:
            print(f"\n发生未知错误: {e}")


if __name__ == "__main__":
    main()
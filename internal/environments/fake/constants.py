class BashErrors:
    CMD_NOT_FOUND = "bash: {cmd}: command not found\n"
    NO_FILE_OR_DIR = "bash: {cmd}: {target}: No such file or directory\n"
    IS_DIRECTORY = "bash: {cmd}: {target}: Is a directory\n"
    PERMISSION_DENIED = "bash: {cmd}: {target}: Permission denied\n"

class Prompts:
    UBUNTU_22_04 = "Welcome to Ubuntu 22.04 LTS (GNU/Linux)\r\n$"
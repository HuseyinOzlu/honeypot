import unittest
from internal.environments.fake.vfs import VirtualFileSystem
from internal.environments.fake.shell import FakeShell

class TestVirtualFileSystemAndShell(unittest.TestCase):
    def setUp(self):
        self.vfs = VirtualFileSystem()
        self.shell = FakeShell(self.vfs)

    def test_initial_cwd(self):
        self.assertEqual(self.vfs.cwd, "/root")
        output = self.shell.execute("pwd")
        self.assertEqual(output.strip(), "/root")

    def test_whoami_and_id(self):
        self.assertEqual(self.shell.execute("whoami").strip(), "root")
        self.assertIn("uid=0(root)", self.shell.execute("id"))

    def test_file_create_and_read(self):
        # Simulate echo redirect into file
        self.shell.execute("echo 'secret payload' > /root/test.txt")
        content = self.vfs.read_file("/root/test.txt")
        self.assertEqual(content.strip(), "secret payload")

        # Verify cat returns the same
        cat_out = self.shell.execute("cat /root/test.txt")
        self.assertEqual(cat_out.strip(), "secret payload")

    def test_cd_and_ls(self):
        self.shell.execute("cd /etc")
        self.assertEqual(self.vfs.cwd, "/etc")
        ls_out = self.shell.execute("ls")
        self.assertIn("passwd", ls_out)
        self.assertIn("issue", ls_out)

if __name__ == "__main__":
    unittest.main()

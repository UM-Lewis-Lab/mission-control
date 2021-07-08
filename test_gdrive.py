from pathlib import Path

from mission_control import gdrive

test_file = Path("~/Downloads/test.txt").expanduser().resolve()
test_file.write_text("Hello world!")

client = gdrive.connect()
fid = client.upload(test_file, "this-is-a-test.bin", folder_name="hello-world")
client.download(test_file.with_name("test2.txt"), file_name="this-is-a-test.bin")

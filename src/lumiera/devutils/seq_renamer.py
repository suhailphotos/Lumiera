import os
import re
from typing import Optional, Callable, Pattern

class SeqRenamer:
    """
    A utility for bulk renaming files in a given directory (and optionally its subdirectories)
    based on a regular expression match and a replacement pattern or transformation function.
    """
    def __init__(
        self,
        source_folder: str,
        input_regex: str,
        output_pattern: Optional[str] = None,
        recursive: bool = False,
        transform_func: Optional[Callable[[re.Match], str]] = None
    ):
        """
        Parameters:
          source_folder: The path to the folder where files will be renamed.
          input_regex: A regex pattern to match filenames.
          output_pattern: A replacement pattern to generate new filenames.
                          If provided, it will be used with re.sub.
          recursive: Whether to process files recursively in subfolders.
          transform_func: An optional function that takes a re.Match object and returns
                          the new filename. If provided, this overrides output_pattern.
        """
        self.source_folder = source_folder
        self.input_regex: Pattern = re.compile(input_regex)
        self.output_pattern = output_pattern
        self.recursive = recursive
        self.transform_func = transform_func

    def rename_files(self):
        """
        Walks through the source_folder and renames files whose names match input_regex.
        If transform_func is provided, it is used to compute the new name; otherwise,
        output_pattern (if provided) is used as the replacement string in re.sub.
        """
        for root, dirs, files in os.walk(self.source_folder):
            for filename in files:
                match = self.input_regex.search(filename)
                if match:
                    if self.transform_func:
                        new_name = self.transform_func(match)
                    elif self.output_pattern is not None:
                        new_name = self.input_regex.sub(self.output_pattern, filename)
                    else:
                        print(f"Skipping {filename}: no output pattern or transform function provided.")
                        continue

                    old_path = os.path.join(root, filename)
                    new_path = os.path.join(root, new_name)
                    
                    if os.path.exists(new_path):
                        print(f"Skipping {old_path}: target file {new_path} already exists.")
                    else:
                        print(f"Renaming:\n  {old_path}\n  -> {new_path}")
                        os.rename(old_path, new_path)
            if not self.recursive:
                break

if __name__ == "__main__":
    # Example usage:
    #
    # Source folder with files:
    # /Users/suhail/Library/CloudStorage/Dropbox/threeD/projects/12_hdr_gain_map/usd/assets/dev/macbook_pro/lkdev/scene_files/render
    #
    # Files like:
    #   macbook_pro_v1.karmarendersettings.0001.exr
    #   macbook_pro_v1.karmarendersettings.0002.exr
    #   ...
    #
    # We want to rename them to:
    #   hdr_gain_map_01.exr
    #   hdr_gain_map_02.exr
    #   ...
    #
    # Define the input regex that captures the numeric sequence.
    source_folder = "/Users/suhail/Library/CloudStorage/Dropbox/threeD/projects/12_hdr_gain_map/usd/assets/dev/macbook_pro/lkdev/scene_files/render"
    input_regex = r"macbook_pro_v1\.karmarendersettings\.(\d{4})\.exr"
    
    # A transformation function that converts the captured number to an integer
    # and then formats it with 2 digits.
    def transform(match: re.Match) -> str:
        number_str = match.group(1)
        number = int(number_str)
        return f"hdr_gain_map_{number:02d}.exr"
    
    # Instantiate the SeqRenamer.
    renamer = SeqRenamer(
        source_folder=source_folder,
        input_regex=input_regex,
        recursive=False,
        transform_func=transform
    )
    
    # Run the renaming process.
    renamer.rename_files()

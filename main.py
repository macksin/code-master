import os
import subprocess
import argparse
from collections import defaultdict

def get_repo_dir(repo_url, branch=None):
    """Retrieve or clone the repository to a local cache directory.
    
    Args:
        repo_url: URL of the repository to clone
        branch: Optional branch name to checkout
    """
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    cache_dir = './repo_cache'
    os.makedirs(cache_dir, exist_ok=True)
    repo_path = os.path.join(cache_dir, repo_name)
    
    if not os.path.exists(repo_path):
        print(f"Cloning repository {repo_url} to {repo_path}")
        clone_cmd = ['git', 'clone', repo_url, repo_path]
        if branch:
            clone_cmd.extend(['--branch', branch])
        subprocess.run(clone_cmd, check=True)
    else:
        print(f"Using existing repository at {repo_path}")
        if branch:
            print(f"Checking out branch: {branch}")
            subprocess.run(['git', '-C', repo_path, 'fetch'], check=True)
            subprocess.run(['git', '-C', repo_path, 'checkout', branch], check=True)
            subprocess.run(['git', '-C', repo_path, 'pull'], check=True)
    
    return repo_path

def search_word_in_repo(repo_path, word, allowed_extensions=None, ignore_case=False):
    """Search for a word in the repository and log statistics for searched files."""
    collected_files = []
    # Initialize a defaultdict to store extension statistics
    extension_stats = defaultdict(lambda: {'files': 0, 'lines': 0})
    
    # Log the start of the search with context
    extensions_msg = f"files with extensions {', '.join(allowed_extensions)}" if allowed_extensions else "all text files"
    case_msg = "(case-insensitive)" if ignore_case else ""
    print(f"Searching for '{word}' {case_msg} in {extensions_msg} in repository at {repo_path}")
    
    # Walk through the repository
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d != '.git']  # Skip .git directory
        for file in files:
            file_path = os.path.join(root, file)
            extension = os.path.splitext(file)[1].lower()
            
            # Skip files that don’t match allowed extensions (if specified)
            if allowed_extensions and extension not in allowed_extensions:
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Count lines (add 1 for the last line if it doesn’t end with \n)
                    num_lines = content.count('\n') + 1
                    
                    # Update statistics for this extension
                    extension_stats[extension]['files'] += 1
                    extension_stats[extension]['lines'] += num_lines
                    
                    # Perform the word search
                    search_content = content.lower() if ignore_case else content
                    search_word = word.lower() if ignore_case else word
                    if search_word in search_content:
                        rel_path = os.path.relpath(file_path, repo_path)
                        collected_files.append((rel_path, content))
                        print(f"Found in: {rel_path}")
            except UnicodeDecodeError:
                # Skip binary files without counting them
                pass
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    # Log the statistics
    if not extension_stats:
        print("No files found matching the search criteria.")
    else:
        print("Statistics for searched files:")
        for ext in sorted(extension_stats.keys()):
            files = extension_stats[ext]['files']
            lines = extension_stats[ext]['lines']
            print(f"{ext}: {files} files, {lines} lines")
        total_files = sum(stats['files'] for stats in extension_stats.values())
        total_lines = sum(stats['lines'] for stats in extension_stats.values())
        print(f"Total: {total_files} files, {total_lines} lines")
    
    print(f"Total files with '{word}': {len(collected_files)}")
    return collected_files

def write_output(collected_files, output_file='output.txt'):
    """Write the contents of files containing the word to a text file."""
    with open(output_file, 'w', encoding='utf-8') as out_file:
        for rel_path, content in collected_files:
            out_file.write(f'<filename>{rel_path}</filename>\n')
            out_file.write(content)
            out_file.write('\n')
    print(f"Output written to {output_file}")

def main():
    """Parse arguments and execute the search."""
    parser = argparse.ArgumentParser(description='Search for a word in a GitHub repository.')
    parser.add_argument('repo_url', help='GitHub repository URL (e.g., https://github.com/user/repo.git)')
    parser.add_argument('word', help='Word to search for')
    parser.add_argument('--extensions', '-e', help='Comma-separated list of extensions (e.g., .py,.txt)')
    parser.add_argument('--output', '-o', default='output.txt', help='Output file (default: output.txt)')
    parser.add_argument('--ignore-case', '-i', action='store_true', help='Case-insensitive search')
    parser.add_argument('--branch', '-b', help='Specific branch to explore')
    args = parser.parse_args()

    repo_path = get_repo_dir(args.repo_url, args.branch)
    allowed_extensions = [ext.lower() for ext in args.extensions.split(',')] if args.extensions else None
    collected_files = search_word_in_repo(repo_path, args.word, allowed_extensions, args.ignore_case)
    write_output(collected_files, args.output)

if __name__ == '__main__':
    main()
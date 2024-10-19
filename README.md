# Installation Guide

This guide will help you install all required dependencies for this project using `requirements.txt` file across different operating systems.

## Prerequisites

Before installing the requirements, make sure you have:
- Python 3.7 or higher installed
- pip (Python package installer) installed
- Git (optional, for cloning the repository)

## Installation Steps

### Windows

1. Open Command Prompt or PowerShell
2. Navigate to project directory:
```cmd
cd path\to\your\project
```
3. (Optional) Create and activate virtual environment:
```cmd
python -m venv venv
.\venv\Scripts\activate
```
4. Install requirements:
```cmd
pip install -r requirements.txt
```

### macOS/Linux

1. Open Terminal
2. Navigate to project directory:
```bash
cd path/to/your/project
```
3. (Optional) Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```
4. Install requirements:
```bash
pip3 install -r requirements.txt
```

### Using Conda

1. Open Conda prompt/terminal
2. Navigate to project directory:
```bash
cd path/to/your/project
```
3. Create and activate conda environment (optional):
```bash
conda create --name yourenvname python=3.9
conda activate yourenvname
```
4. Install requirements:
```bash
pip install -r requirements.txt
```

## Troubleshooting

### Common Issues

1. **Permission Error**
   - Windows: Run Command Prompt as Administrator
   - macOS/Linux: Use `sudo pip3 install -r requirements.txt`

2. **SSL Certificate Error**
   ```bash
   pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
   ```

3. **Pip Not Found**
   - Ensure Python and pip are added to your system's PATH
   - Try using `python -m pip install -r requirements.txt`

### Offline Installation

If you need to install packages in an environment without internet access:

1. Download packages on a machine with internet:
```bash
pip download -r requirements.txt -d ./packages
```

2. Transfer the `packages` directory to the offline machine

3. Install from the downloaded files:
```bash
pip install --no-index --find-links packages -r requirements.txt
```

## Package List

The following packages will be installed:
- aiohttp
- tqdm
- fake_useragent
- aiohttp_socks

## Support

If you encounter any issues during installation, please:
1. Check if you're using the correct Python version
2. Ensure all prerequisites are installed
3. Create an issue in the repository with the error message and your system details

## License

This project is licensed under the MIT License - see the LICENSE file for details

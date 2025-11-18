from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="s3bridge",
    version="1.0.0",
    author="Universal S3 Team",
    description="Account-agnostic credential service for secure S3 access",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "boto3>=1.26.0",
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "universal-s3-setup=scripts.setup:main",
            "universal-s3-service=scripts.service_manager:main",
            "universal-s3-add-service=scripts.add_service:main",
            "universal-s3-list-services=scripts.list_services:main",
            "universal-s3-remove-service=scripts.remove_service:main",
            "universal-s3-edit-service=scripts.edit_service:main",
            "universal-s3-status=scripts.service_status:main",
            "universal-s3-test=scripts.test_service:main",
            "universal-s3-backup=scripts.backup_restore:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["templates/*.yaml", "lambda_functions/*.py"],
    },
)
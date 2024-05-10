## Setting up the Runtime Environment

This project is developed using Python v3.10. The complete Python dependency packages can be found in requirements.txt.

**Here are the detailed installation instructions (using Ubuntu operating system as an example):**

### Installing Miniconda

```shell
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh
```

After the installation is complete, it is recommended to create a new Python virtual environment
named `character-dialogue-glm`.

```shell
conda create -n character-dialogue-glm python=3.10
```

### Activate the environment

```shell
conda activate character-dialogue-glm 
```

You will need to activate this environment every time you use it.

### Installing Python Dependency Packages

#### Run the following command in the `character-dialogue-glm` directory

```shell
pip install -r requirements.txt
```

### Running the Project

```shell
streamlit run --server.address 127.0.0.1 src/once_upon_in_shu_han.py
```

### Successful Startup

```shell
  You can now view your Streamlit app in your browser.
  URL: http://127.0.0.1:8502
```

Access through the awakened browser

### Page

![img.png](resources/image/image.png)

## License

This project is licensed under the terms of the Apache-2.0 license. See the LICENSE file for more details.

## FAQ

* Why is the toggle for `Generate character avatars based on character settings` on the page inoperable?
    * As mentioned in the `help` section of the `toggle`, if you ensure that your `ApiKey` has the authorization to generate images using CogView and has sufficient balance, please set the disabled attribute of this `toggle` to `False` in [once_upon_in_shu_han.py](src%2Fonce_upon_in_shu_han.py) file.
```python
    generate_picture_switch = st.toggle("是否根据人设生成人物头像", value=False, disabled=False,
                                        help='请确保apiKey拥有智谱CogView生成图的权限并且余额充足,否则将会使用默认头像')
```
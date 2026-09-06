I have taken a more methodical approach to documenting my work after reading this [document](https://www.writethedocs.org/guide/writing/beginners-guide-to-docs/). 


The more I look into this field of FinTech, the more interesting it gets. As boring as it sounds, I am sure that innovation is lurking somewhere in the corner. 

Today is about:
- getting my feet wet with the native github cli command `gh` so that I can learn to create pr's more quickly. I used the following command to install the cli:

```bash
(type -p wget >/dev/null || (sudo apt update && sudo apt install wget -y)) \
	&& sudo mkdir -p -m 755 /etc/apt/keyrings \
	&& out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
	&& cat $out | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
	&& sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
	&& sudo mkdir -p -m 755 /etc/apt/sources.list.d \
	&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
	&& sudo apt update \
	&& sudo apt install gh -y
```

and the following to upgrade:

```bash
sudo apt update
sudo apt install gh
```


- doing more research on existing sanctions-screening software out there.



At the moment, my current idea of the project is to build a 
```
full-stack application for compliance officers by surfacing hidden 2nd-degree agents risks via some interactive network visualizer like NetworkX. This is so that compliance officers can audit every connection to individuals who get flagged by the system. 
```

This will likely change in the upcoming days after I do more research.
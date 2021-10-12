# Ellis  
  Ellis is a rather simple central server and protocol for NationStates
recruiitment purposes

### Features  
- Module System to allow somewhat easy extenstions.
- Simple to use protocol that is also relatively easy to implement.
- A simple, but powerful, filtering/blacklisting system, with sane defaults.
- A simple to use Auto-Telegram System that implements with it.

### Requirements  
- Python 3.9 or later
- An internet connection

### Development Requirements
- Python 3.9 or later
- An Internet Connection
- Pytest
- Pylint
- Flake8

### License and Copyright  
  All code is licensed under the MIT (Expat) License, see LICENSE for more Information.
  All Copyright is held by their respective authors.

## QnA  
##### Why should I use Ellis over [INSERT PROGRAM HERE]?  
  Well, you probably shouldn't, however there are a few reasons you should:
   - You wish to add in other ways for people to recruit, and need to filter the same way.
   - You need something that is headless first,
   - You need something that will just run on a default linux installation.

##### Why did you not just use [INSERT PROGRAM HERE]?  
  Because I didn't know about it, and I had specific requirements when developing
this. I needed something that didn't require me installing additional software on
my servers, and I needed somethign I could plug other things into later.

##### Why did you release this?  
  Because I felt others might be able to use it as well.

##### Why did you not use [INSERT LIBRARY HERE]?  
  Ease. I wanted to ensure that it was as minimal-dependency as possible,
to make deploying it for myself a bit easier -- at least where possible.
Additionally, the overall surface size is pretty small, so pulling in a dependency
that is the same size, or larger, to use a small portion of the functionality
didn't really feel right.

##### How does the Blaclisting System Work?  
  The blacklist file is a simple UTF-8 JSON file. The root attributes is the lowercase name
of a NationStates nation shard (specifically one that is available in a default request,
with no shards requested). It has an object with two list attributes that are lowercase and named
exact and partial. Any string that is listed in the exact list will be tested to see if that field
is an exact match (although the match is casefolded). Any string that is listed in the partial list
will be tested to see if that string is in that field at all, albeit casefolded. 

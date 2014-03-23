Gherkin2Testrail
================

Sublime-text plugin to translate Gherkin .feature to Testrail XML

Usage
---

* Put all files in your Packages/Gherkin2Testrail directory (/Users/{user}/Library/Application Support/Sublime Text 2/Packages)
* Menu items can be found under Tools>Testrail
* To convert to Testrail XML, open the Console and execute the command
```
view.run_command('gherkintotestrailxml')
```
* To Import to a currently existing Testrail project, open the Console and execute the command
```
view.run_command('gherkintotestrailimportsuite')
```
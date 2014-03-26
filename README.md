Gherkin2Testrail
================

Sublime-text plugin to translate Gherkin .feature to Testrail XML

Usage
---

* Put all files in your Packages/Gherkin2Testrail directory
* Menu items can be found under Tools>Testrail
* To convert to Testrail XML, open the Console and execute the command
```
view.run_command('gherkin2testrailXml')
```
* To perform a bulk import (from all files open in a Sublime Text Group), execute the command:
```
view.run_command('gherkin2testrailBulk')
```
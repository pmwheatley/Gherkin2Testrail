from testrail import *

import sublime, sublime_plugin
import re



class Feature(object):
	""" An object which holds a single Feature """
	def __init__(self, text):
		
		self.tags = None
		self.name = None
		self.description = ""

		self.background = None
		self.scenarios = []

		sections = re.split('\n\n', text)

		for section in sections:
			if re.search('Feature:', section):
				self.tags = re.search('(@.*)', section).group(1).split(' ')
				self.name = re.search('Feature: (.*)', section).group(1)
				self.description = re.sub('(\t| ( )+)', '', re.search('Feature.*\n((?:\s*(?:\w.*\n?))+)', section).group(1))

			if re.search('\s*Background', section):
				self.background = Background(section)

			if re.search('\s*Scenario', section):
				self.scenarios.append(Scenario(section))

	def __str__(self):
		text = "%s\nFeature: %s\n%s\n\n%s\n\n" % (' '.join(self.tags), self.name, re.sub('\n', '\n\t', '\t' + self.description), self.background)
		for scenario in self.scenarios:
			text = text + str(scenario) + '\n\n'
		return text

class Background(object):
	def __init__(self, text):
		if re.match('(@.*)', text):
			self.tags = re.match('(@.*)', text).group(1).split(' ')
		else:
			self.tags = ""
		
		self.name = re.search('\s*Background:(?: )?(.*)', text).group(1)
		self.steps = []

		number = 1
		while number:
			text, number = re.subn('((Given|When|Then)(.*\n)+?\s+)And', r'\1\2', text)

		steps = re.split('(Given|When|Then)', re.sub('^(\t| ( )+)', '', re.search('Background.*\n((?:.*\n?)+)', text).group(1)))

		for i in range(1, len(steps), 2):
			self.steps.append(Step(steps[i], steps[i+1].strip()))

	def __str__(self):
		tags = ""
		for i in self.tags:
			tags = tags + i + ' '
		steps = ""
		for i in self.steps:
			steps = steps + '\n\t' + str(i)
		
		if tags:
			return '%s\nBackground: %s%s' % (tags, self.name, steps)
		else:
			return 'Background: %s%s' % (self.name, steps)

class Scenario(object):
	def __init__(self, text):
		if re.match('(@.*)', text):
			self.tags = re.match('(@.*)', text).group(1).split(' ')
		else:
			self.tags = ""
		
		self.name = re.search('\s*Scenario:(?: )?(.*)', text).group(1)
		self.steps = []

		number = 1
		while number:
			text, number = re.subn('((Given|When|Then)(.*\n)+?\s+)And', r'\1\2', text)

		steps = re.split('(Given|When|Then)', re.sub('^(\t| ( )+)', '', re.search('Scenario.*\n((?:.*\n?)+)', text).group(1)))

		for i in range(1, len(steps), 2):
			self.steps.append(Step(steps[i], steps[i+1].strip()))

	def testrailFormat(self):
		steps = ""
		for i, step in enumerate(self.steps):
			if i > 0 and step.type == self.steps[i-1].type:
				type = '\tAnd'
			else:
				type = step.type
			
			steps = steps + '\n\t' + type + ' ' + step.text + str(step.data)

		return {'title': self.name, 'bdd_tags': self.tags, 'custom_steps': steps}

	def featureFormat(self):
		tags = ""
		for i in self.tags:
			tags = tags + i + ' '
		steps = ""
		for i, step in enumerate(self.steps):
			if i > 0 and step.type == self.steps[i-1].type:
				type = '\tAnd'
			else:
				type = step.type
			
			steps = steps + '\n\t' + type + ' ' + step.text + str(step.data)
		
		if tags:
			return '%s\nScenario: %s%s' % (tags, self.name, steps)
		else:
			return 'Scenario: %s%s' % (self.name, steps)

	def __str__(self):
		return self.featureFormat()

class Step(object):
	def __init__(self, type, text):
		self.type = type
		self.lines = text.splitlines()
		self.text = self.lines[0]


		self.data = Table(self.lines)

	def __str__(self):
		if self.data:
			return self.type + ' ' +  str(self.text) + ' ' + str(self.data)
		else:
			return self.type + ' ' +  str(self.text)

class Table(object):
	def __init__(self, lines):
		self.data = {}

		self.table = []
		for line in lines[1:]:
			self.table.append(re.split('\s*\|\s*', line)[1:-1])

		datakey = []
		if len(lines)>1:
			data = re.split('\s*\|\s*', lines[1])
			for i, key in enumerate(data[1:-1]):
				datakey.append(key)

		datavalue = []
		if len(lines)>2:
			for i, line in enumerate(lines[2:]):
				datavalue.append([])
				data = re.split('\s*\|\s*', line)
				for j, value in enumerate(data[1:-1]):
					datavalue[i].append(value)

		for i in range(0, len(datakey)):
			self.data[datakey[i]] = []
			for j in datavalue:
				if j:
					self.data[datakey[i]].append(j[i])
				else:
					self.data[datakey[i]].append("")
			self.data[datakey[i]].reverse()

	def __str__(self):
		max_length=0
		for row in self.table:
			for entry in row:
				if len(entry) > max_length:
					max_length = len(entry)

		text = ""
		for row in self.table:
			text = text + '\n\t\t\t| '
			for entry in row:
				text = text + entry.ljust(max_length) + ' | '
		return text



class cucumber2testrailCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		allTextRegion = sublime.Region(0, self.view.size())
		text = self.view.substr(allTextRegion).strip()
		self.feature = Feature(text)

		self.view.window().show_input_panel("Enter Credentials [server, username, password]:", "", self.onEnterCredentials, None, None)

	def onEnterCredentials(self, text):
		args = text.split(', ')

		self.client = APIClient(args[0])
		self.client.user = args[1]
		self.client.password = args[2]

		APIProjects = self.client.send_get('get_projects')
		self.projects = []
		for project in APIProjects:
			self.projects.append(str(project['id']) + ' - ' + project['name'])

		self.view.window().show_quick_panel(self.projects, self.onSelectProject)

	def onSelectProject(self, index):
		print "Updating Project\t\t" + self.projects[index]
		self.currProject = index + 1
		
		suite_name = self.feature.name
		suite_description = self.feature.description

		currSuites = self.client.send_get('get_suites/' + str(self.currProject))
		
		suite_id = None
		for x in currSuites:
			if x['name'] == suite_name:
				suite_id = x['id']

		if suite_id == None:
			suite_id = self.client.send_post('add_suite/' + str(self.currProject), {"name": suite_name, "description": suite_description})['id']
			print("Adding new Test Suite\t- id: " + str(suite_id))
		else:
			self.client.send_post('update_suite/' + str(suite_id), {"name": suite_name, "description": suite_description})
			print("Updating Test Suite\t\t- id:" + str(suite_id))

		currSections = self.client.send_get('get_sections/' + str(self.currProject) + '&suite_id=' + str(suite_id))
		section_id = None
		for x in currSections:
			if x['name'] == 'name':
				section_id = x['id']

		if section_id == None:
			section_id = self.client.send_post('add_section/' + str(self.currProject), {"suite_id": suite_id, "name": 'name'})['id']
			print("Adding new Section\t\t- id: " + str(section_id))
		else:
			print("Updating Section\t\t- id: " + str(section_id))

		for scenario in self.feature.scenarios:
			currScenarios = self.client.send_get('get_cases/' + str(self.currProject) + '&suite_id=' + str(suite_id) + '&section_id=' + str(section_id))
			scenario_id = None
			for x in currScenarios:
				if x['id'] == scenario.name:
					scenario_id = x['id']

			if section_id == None:
				section_id = self.client.send_post('add_section/' + str(self.currProject), {"suite_id": suite_id, "name": i[0]})['id']
				print("Adding new Section\t\t- id: " + str(section_id))
			else:
				print("Updating Section\t\t- id: " + str(section_id))

			if scenario_id == None:
		 		scenario_id = self.client.send_post('add_case/' + str(section_id), scenario.testrailFormat())['id']
		 		print("Adding new Test Case\t- id: " + str(scenario_id))
			else:
				self.client.send_post('update_case/' + str(scenario_id), scenario.testrailFormat())
				print("Updating Test Case\t\t- id: " + str(scenario_id))


class gherkintotestrailxmlCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		alltextreg = sublime.Region(0, self.view.size())
		s = self.view.substr(alltextreg).strip()
		s = re.sub(r'&', r'&amp;', s)
		s = re.sub(r'<', r'&lt;', s)
		s = re.sub(r'>', r'&gt;', s)
		s = re.sub(r'"', r'&quot;', s)
		s = re.sub(r'\'', r'&apos;', s)
		s = re.sub(r'Feature: (.*)\n?((.*\n)*(.*))', r'<?xml version="1.0" encoding="UTF-8"?>\n<sections>\n<section>\n\t\t<name>\1</name>\n\t\t<sections>\2\n\t\n\n\n\t</sections>\n</section>\n</sections>', s)
		s = re.sub(r'# (.*)\n((.*\n)*?)\n\n', r'\t\t<section>\n\t\t\t<name>\1</name>\n\t\t\t<cases>\n\2\n\t\t\t</cases>\n\t\t</section>\n', s)
		s = re.sub(r'Scenario( Outline)*: (.*) - (.*)\n((.*\n)*?)\n', r'\t\t\t\t<case>\n\t\t\t\t\t<title>\3</title>\n\t\t\t\t\t<custom>\n\t\t\t\t\t\t<bdd_id>\2</bdd_id>\n\4\t\t\t\t\t</custom>\n\t\t\t\t</case>\n', s)
		s = re.sub(r'(@.*)\n((.*\n)*?.*</bdd_id>)', r'\2\n\t\t\t\t\t\t<bdd_tags>\1</bdd_tags>', s)
		s = re.sub(r'\n.*((?:And|But) (.*))', r'&#xA;\1', s)
		s = re.sub(r'\n\t*(\|(.*)\|)', r'&#xA;\1', s)
		s = re.sub(r'\t*Given (.*)', r'\t\t\t\t\t\t<bdd_given>\1</bdd_given>', s)
		s = re.sub(r'\t*When (.*)', r'\t\t\t\t\t\t<bdd_when>\1</bdd_when>', s)
		s = re.sub(r'\t*Then (.*)', r'\t\t\t\t\t\t<bdd_then>\1</bdd_then>', s)
		s = re.sub(r'\t*Examples:&#xA;(.*)', r'\t\t\t\t\t\t<bdd_examples>\1</bdd_examples>', s)
		self.view.replace(edit, alltextreg, s)

class gherkintotestrailimportsuiteCommand(sublime_plugin.TextCommand):

	def run(self, edit):

		self.view.window().show_input_panel("Enter Credentials [server, username, password]:", "", self.onEnterCredentials, None, None)

	def onEnterCredentials(self, text):
		args = text.split(', ')

		self.client = APIClient(args[0])
		self.client.user = args[1]
		self.client.password = args[2]

		APIProjects = self.client.send_get('get_projects')
		self.projects = []
		for project in APIProjects:
			self.projects.append(str(project['id']) + ' - ' + project['name'])

		self.view.window().show_quick_panel(self.projects, self.onSelectProject)

	def onSelectProject(self, index):
		print "Updating Project\t\t" + self.projects[index]
		self.currProject = index + 1

		alltextreg = sublime.Region(0, self.view.size())
		s = self.view.substr(alltextreg).strip()

		suite_name = re.search(r'Feature: (.*)', s).group(1)
		currSuites = self.client.send_get('get_suites/' + str(self.currProject))
		
		suite_id = None
		for x in currSuites:
			if x['name'] == suite_name:
				suite_id = x['id']
		
		suite_description = re.sub('#( )?', '', re.search(r'Feature.*\n+(?:#\n)?((?:#.*\n)*)', s).group(1))
		print(suite_description)

		if suite_id == None:
			suite_id = self.client.send_post('add_suite/' + str(self.currProject), {"name": suite_name, "description": suite_description})['id']
			print("Adding new Test Suite\t- id: " + str(suite_id))
		else:
			self.client.send_post('update_suite/' + str(suite_id), {"name": suite_name, "description": suite_description})
			print("Updating Test Suite\t\t- id:" + str(suite_id))

		sections = {}
		scenarios = {}
		for i in re.findall(r'# (.*)\n((?:@.*|Scenario.*|##.*)+\n((?:.*\n)*?\n)\n)', s):
			currSections = self.client.send_get('get_sections/' + str(self.currProject) + '&suite_id=' + str(suite_id))
			section_id = None
			for x in currSections:
				if x['name'] == i[0]:
					section_id = x['id']

			if section_id == None:
				section_id = self.client.send_post('add_section/' + str(self.currProject), {"suite_id": suite_id, "name": i[0]})['id']
				print("Adding new Section\t\t- id: " + str(section_id))
			else:
				print("Updating Section\t\t- id: " + str(section_id))

		 	for j in re.findall(r'(?:((?:@.*\n))|#.*)*Scenario(?: Outline)*: (.*) - (.*)\n((?:.*\n)*?)\n', i[1]):
				currScenarios = self.client.send_get('get_cases/' + str(self.currProject) + '&suite_id=' + str(suite_id) + '&section_id=' + str(section_id))
				scenario_id = None
				for x in currScenarios:
					if x['custom_bdd_id'] == j[1]:
						scenario_id = x['id']

		 		tags 		= j[0]
		 		given 		= re.findall(r'\t*Given ((?:.*)(?:\n\t\t(?:And|But) .*)*)', j[3])
		 		when  		= re.findall(r'\t*When ((?:.*)(?:\n\t\t(?:And|But) .*)*)', j[3])
		 		then 		= re.findall(r'\t*Then ((?:.*)(?:\n\t\t(?:And|But) .*)*)', j[3])
		 		examples 	= re.findall(r'\t*Examples:\n((?:\t*.*\n)*)', j[3])

		 		scenarios[j[1]] = {'custom_bdd_id': j[1], 'title': j[2]}
		 		if (given): 	scenarios[j[1]]['custom_bdd_given'] = given[0]
		 		if (when): 		scenarios[j[1]]['custom_bdd_when'] = when[0]
		 		if (then): 		scenarios[j[1]]['custom_bdd_then'] = then[0]
		 		if (examples): 	scenarios[j[1]]['custom_bdd_examples'] = examples[0]
		 		if (tags): 		scenarios[j[1]]['custom_bdd_tags'] = tags

				if scenario_id == None:
			 		scenario_id = self.client.send_post('add_case/' + str(section_id), scenarios[j[1]])['id']
			 		print("Adding new Test Case\t- id: " + str(scenario_id))
				else:
					self.client.send_post('update_case/' + str(scenario_id), scenarios[j[1]])
					print("Updating Test Case\t\t- id: " + str(scenario_id))

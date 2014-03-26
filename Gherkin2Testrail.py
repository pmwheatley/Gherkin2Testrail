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

		testrail_sections = re.split('#### (.*)', text)

		if re.search('Feature:', testrail_sections[0]):
			self.name = re.search('Feature: (.*)', testrail_sections[0]).group(1)
			if re.search('(@.*)', testrail_sections[0]):
				self.tags = re.search('(@.*)', testrail_sections[0]).group(1).split(' ')
			if re.search('Feature.*\n((?:\s*(?:\w.*\n?))+)', testrail_sections[0]):
				self.description = re.sub('(\t| ( )+)', '', re.search('Feature.*\n((?:\s*(?:\w.*\n?))+)', testrail_sections[0]).group(1))


		for i in range(1, len(testrail_sections), 2):
			text_sections = re.split('\n\n', testrail_sections[i+1])

			for text_section in text_sections:
				if re.search('\s*Background', text_section):
					self.background = Background(text_section)

				if re.search('\s*Scenario', text_section):
					self.scenarios.append(Scenario(text_section, testrail_sections[i]))

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
			text, number = re.subn('((Given|When|Then)(.*\n)+?\s+)(And|But)', r'\1\2', text)

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
	def __init__(self, text, testrail_section):

		self.testrail_section = testrail_section

		if re.search('^\s*(@.*)', text):
			self.tags = re.search('^\s*(@.*)', text).group(1).split(' ')
		else:
			self.tags = ""
		
		self.name = re.search('\s*Scenario(?: Outline)?:(?: )?(.*)', text).group(1)
		self.steps = []
		self.examples = ""

		number = 1
		while number:
			text, number = re.subn('((Given|When|Then)(.*\n)+?\s+)(And|But)', r'\1\2', text)

		if re.search('\s*Examples:.*\n((?:.*\n?)+)', text):
			self.examples = Table(re.sub('^(\t| ( )+)', '', re.search('\s*Examples:.*\n((?:.*\n?)+)', text).group(1)).splitlines())

		steps = re.split('(Given|When|Then|Examples:\n)', re.sub('^(\t| ( )+)', '', re.search('Scenario.*\n((?:.*\n?)+)?(?:Examples:.*)?', text).group(1)))

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

		bdd_id = re.search('(.*) - .*', self.name).group(1)
		self.name = re.search('.* - (.*)', self.name).group(1)

		givenSteps = []
		whenSteps = []
		thenSteps = []
		for step in self.steps:
			if step.type == "Given":
				givenSteps.append(str(step))
			elif step.type == "When":
				whenSteps.append(str(step))
			elif step.type == "Then":
				thenSteps.append(str(step))

		given = '\n'.join(givenSteps)
		when = '\n'.join(whenSteps)
		then = '\n'.join(thenSteps)

		examples = str(self.examples)

		return {'title': self.name, 'custom_bdd_id': bdd_id, 'custom_bdd_tags': ' '.join(self.tags), 'custom_bdd_given': given, 'custom_bdd_when': when, 'custom_bdd_then': then, 'custom_bdd_examples': examples}

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
		
		scenarioText = "Scenario:"
		for i in self.steps:
			if i.data:
				scenarioText = "Scenario Outline:"

		if tags:
			return '%s\n%s %s%s' % (tags, scenarioText, self.name, steps)
		else:
			return '%s %s%s' % (scenarioText, self.name, steps)

	def __str__(self):
		return self.featureFormat()

class Step(object):
	def __init__(self, type, text):
		self.type = type
		self.lines = text.splitlines()
		self.text = self.lines[0]

		self.data = Table(self.lines[1:])

	def __str__(self):
		if self.data:
			return self.type + ' ' +  str(self.text) + ' ' + str(self.data)
		else:
			return self.type + ' ' +  str(self.text)

class Table(object):
	def __init__(self, lines):
		self.data = {}

		self.table = []
		for line in lines:
			self.table.append(re.split('\s*\|\s*', line)[1:-1])

		datakey = []
		if len(lines)>0:
			data = re.split('\s*\|\s*', lines[0])
			for i, key in enumerate(data[1:-1]):
				datakey.append(key)

		datavalue = []
		if len(lines)>1:
			for i, line in enumerate(lines[1:]):
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
			text = text + '\n    | '
			for entry in row:
				text = text + entry.ljust(max_length) + ' | '
		return text



class gherkin2testrailbulkCommand(sublime_plugin.TextCommand):
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

		self.view.window().show_input_panel("Enter Tags to upload [blank for all]:", "", self.onSelectTags, None, None)

	def onSelectTags(self, text):
		if (len(text) > 0):
			args = text.split(' ')
			self.tags = args
		else:
			self.tags = []

		self.view.window().show_quick_panel(self.projects, self.onSelectProject)

	def onSelectProject(self, index):
		print "Updating Project\t\t\t" + self.projects[index]
		self.currProject = index + 1

		APISuites = self.client.send_get('get_suites/' + str(self.currProject))
		self.suites = []
		for suite in APISuites:
			self.suites.append(str(suite['id']) + ' - ' + suite['name'])

		self.view.window().show_quick_panel(self.suites, self.onSelectSuite)

	def onSelectSuite(self, index):
		print "Updating Suite\t\t\t\t" + self.suites[index]
		suite_id = self.suites[index].split(' - ')[0]

		for view in self.view.window().views_in_group(self.view.window().active_group()):

			allTextRegion = sublime.Region(0, view.size())
			text = view.substr(allTextRegion).strip()
			feature = Feature(text)

			currSections = self.client.send_get('get_sections/' + str(self.currProject) + '&suite_id=' + str(suite_id))

			section_id = None
			for x in currSections:
				if ((x['name'] == feature.name) and (x['parent_id'] == None)):
					section_id = x['id']

			if section_id == None:
				section_id = self.client.send_post('add_section/' + str(self.currProject), {"suite_id": suite_id, "name": feature.name})['id']
				print("Adding new Section\t\t\t- id: " + str(section_id))
			else:
				print("Updating Section\t\t\t- id: " + str(section_id))

			for scenario in feature.scenarios:

				if (len(self.tags) == 0) or (len(set(scenario.tags).intersection(self.tags)) > 0):

					currSections = self.client.send_get('get_sections/' + str(self.currProject) + '&suite_id=' + str(suite_id))

					subsection_id = None
					for x in currSections:
						if ((x['name'] == scenario.testrail_section) and (x['parent_id'] == section_id)):
							subsection_id = x['id']

					if subsection_id == None:
						subsection_id = self.client.send_post('add_section/' + str(self.currProject), {"suite_id": suite_id, "parent_id": section_id, "name": scenario.testrail_section})['id']
						print("Adding new SubSection\t\t- id: " + str(subsection_id))
					else:
						print("Updating SubSection\t\t\t- id: " + str(subsection_id))

					currScenarios = self.client.send_get('get_cases/' + str(self.currProject) + '&suite_id=' + str(suite_id) + '&section_id=' + str(subsection_id))
					scenario_id = None
					for x in currScenarios:
						if x['custom_bdd_id'] == re.search('(.*) - .*', scenario.name).group(1):
							scenario_id = x['id']

					if scenario_id == None:
						scenario_id = self.client.send_post('add_case/' + str(subsection_id), scenario.testrailFormat())['id']
						print("Adding new Test Case\t\t- id: " + str(scenario_id))
					else:
						self.client.send_post('update_case/' + str(scenario_id), scenario.testrailFormat())
						print("Updating Test Case\t\t\t- id: " + str(scenario_id))


class gherkin2testrailxmlCommand(sublime_plugin.TextCommand):
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

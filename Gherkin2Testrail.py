from testrail import *

import sublime, sublime_plugin
import re

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


class gtt_generateids(sublime_plugin.TextCommand):

	
	def run(self, edit):
        
		print "Generate Scenario IDs"
        
		# s = File content
		alltextreg = sublime.Region(0, self.view.size())
		s = self.view.substr(alltextreg).strip()
	
		# Get featureID    
		featureID = re.search(r'^# (.*)', s).group(1)

		self.globalCounter = 0		
		print("global globalCounter = %d")%(self.globalCounter)

		# regex replacer function
		def dashrepl(matchobj):
			print("func globalCounter = %d")%(self.globalCounter)

			self.globalCounter += 1			
			globalCounterStr = ("%03d")%(self.globalCounter)
			
			return matchobj.group(1) + ': ' + featureID + globalCounterStr + ' - ' + matchobj.group(3)

		# Change IDs to new ID
		s = re.sub(r'(Scenario|Scenario Outline): .*(\d{3}) - (.*)', dashrepl, s)

		# Change changes
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
		self.currProject = int(self.projects[index].split(' ')[0])
		print (str(self.currProject))

		# s = File content
		alltextreg = sublime.Region(0, self.view.size())
		s = self.view.substr(alltextreg).strip()
        
		suite_name = re.search(r'Feature: (.*)', s).group(1)
		currSuites = self.client.send_get('get_suites/' + str(self.currProject))
        
		# Get Suite ID
		suite_id = None
		for x in currSuites:
			if x['name'] == suite_name:
				suite_id = x['id']
        
		suite_description = re.sub('#( )?', '', re.search(r'Feature.*\n+(?:#\n)?((?:#.*\n)*)', s).group(1))
		print(suite_description)
        
		# Check if Suite exists
		if suite_id == None:
			# Add Suite
			suite_id = self.client.send_post('add_suite/' + str(self.currProject), {"name": suite_name, "description": suite_description})['id']
			print("Adding new Test Suite\t- id: " + str(suite_id))
		else:
			self.client.send_post('update_suite/' + str(suite_id), {"name": suite_name, "description": suite_description})
			print("Updating Test Suite\t\t- id:" + str(suite_id))
        
		sections = {}
		scenarios = {}
        
		# Parse Feature file by Sections
		for i in re.findall(r'# (.*)\n((?:@.*|Scenario.*|##.*)+\n((?:.*\n)*?\n)\n)', s):
            
			# i[0] = Section name
			# i[1] = Section content
            
			# Get Sections from TestRails
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
            
			# Parse actual Section by Scenarios
		 	for j in re.findall(r'(?:((?:@.*\n))|#.*)*Scenario(?: Outline)*: (.*) - (.*)\n((?:.*\n)*?)\n', i[1]):
                
		 		# j[0] = Tags
		 		# j[1] = Scenario ID
		 		# j[2] = Scenario String
		 		# j[3] = Scenario Content
                
		 		# Get Scenarios from TestRail
				currScenarios = self.client.send_get('get_cases/' + str(self.currProject) + '&suite_id=' + str(suite_id) + '&section_id=' + str(section_id))
				scenario_id = None
				for x in currScenarios:
					if x['custom_bdd_id'] == j[1]:
						scenario_id = x['id']
                
				# Parse actual Scenario by parts
		 		tags 		= j[0]
		 		given 		= re.findall(r'\t*Given ((?:.*)(?:\n\t\t(?:And|But) .*)*)', j[3])
		 		when  		= re.findall(r'\t*When ((?:.*)(?:\n\t\t(?:And|But) .*)*)', j[3])
		 		then 		= re.findall(r'\t*Then ((?:.*)(?:\n\t\t(?:And|But) .*)*)', j[3])
		 		examples 	= re.findall(r'\t*Examples:\n((?:\t*.*\n)*)', j[3])
                
		 		# Create the Scenario object for TestRail upload
		 		scenarios[j[1]] = {'custom_bdd_id': j[1], 'title': j[2]}
		 		if (given): 	scenarios[j[1]]['custom_bdd_given'] = given[0]
		 		if (when): 		scenarios[j[1]]['custom_bdd_when'] = when[0]
		 		if (then): 		scenarios[j[1]]['custom_bdd_then'] = then[0]
		 		if (examples): 	scenarios[j[1]]['custom_bdd_examples'] = examples[0]
		 		if (tags): 		scenarios[j[1]]['custom_bdd_tags'] = tags
                
		 		# Add/Update TestRail testcase
				if scenario_id == None:
			 		scenario_id = self.client.send_post('add_case/' + str(section_id), scenarios[j[1]])['id']
			 		print("Adding new Test Case\t- id: " + str(scenario_id))
				else:
					self.client.send_post('update_case/' + str(scenario_id), scenarios[j[1]])
					print("Updating Test Case\t\t- id: " + str(scenario_id))


class gherkintotestrailimportsmoketests(sublime_plugin.TextCommand):
    
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
        
		# s = File content
		alltextreg = sublime.Region(0, self.view.size())
		s = self.view.substr(alltextreg).strip()
        
		suite_name = "Smoke Test"
		currSuites = self.client.send_get('get_suites/' + str(self.currProject))
        
        
		# Get Suite ID
		suite_id = None
		for x in currSuites:
			if x['name'] == suite_name:
				suite_id = x['id']
        
        
		# Check if 'Smoke Tests' suite exists
		if suite_id == None:
			# Add 'Smoke Tests' suite
			suite_id = self.client.send_post('add_suite/' + str(self.currProject), {"name": suite_name})['id']
			print("Adding new Test Suite\t- id: " + str(suite_id))
		else:
			# Update 'Smoke Tests' suite
			print("Updating Test Suite\t\t- id:" + str(suite_id))
        
        
		# FeatureFile: Feature name -> Section in 'Smoke Tests' suite
		featureFile_featureName = re.search(r'Feature: (.*)', s).group(1)
        
		# Get Sections from TestRails
		smokeTestsSections = self.client.send_get('get_sections/' + str(self.currProject) + '&suite_id=' + str(suite_id))
        
		# Check if Section exists
		smokeTestsSection_id = None
		for x in smokeTestsSections:
			if x['name'] == featureFile_featureName:
				smokeTestsSection_id = x['id']
        
		# Add/Update section
		if smokeTestsSection_id == None:
			smokeTestsSection_id = self.client.send_post('add_section/' + str(self.currProject), {"suite_id": suite_id, "name": featureFile_featureName})['id']
			print("Adding new Section\t\t- id: " + str(smokeTestsSection_id))
		else:
			print("Updating Section\t\t- id: " + str(smokeTestsSection_id))
        
        
		sections = {}
		scenarios = {}
        
        
		# Parse Feature file by Sections
		for i in re.findall(r'# (.*)\n##+\n((?:.*\n)*?\n)\n', s):
            
            
			# Parse actual Section by Scenarios
		 	for j in re.findall(r'((?:@.*)\n)*Scenario(?: Outline)*: (.*) - (.*)\n((?:.*\n)*?)\n', i[1]):
                
		 		# j[0] = Tags
		 		# j[1] = Scenario ID
		 		# j[2] = Scenario String
		 		# j[3] = Scenario Content
                
		 		# Get Scenarios from TestRail
				currScenarios = self.client.send_get('get_cases/' + str(self.currProject) + '&suite_id=' + str(suite_id) + '&section_id=' + str(smokeTestsSection_id))
				scenario_id = None
				for x in currScenarios:
					if x['custom_bdd_id'] == j[1]:
						scenario_id = x['id']
                
				# Parse actual Scenario by parts
		 		tags 		= j[0]
		 		given 		= re.findall(r'\t*Given ((?:.*)(?:\n\t\t(?:And|But) .*)*)', j[3])
		 		when  		= re.findall(r'\t*When ((?:.*)(?:\n\t\t(?:And|But) .*)*)', j[3])
		 		then 		= re.findall(r'\t*Then ((?:.*)(?:\n\t\t(?:And|But) .*)*)', j[3])
		 		examples 	= re.findall(r'\t*Examples:\n((?:\t*.*\n)*)', j[3])
                
		 		# Create the Scenario object for TestRail upload
		 		scenarios[j[1]] = {'custom_bdd_id': j[1], 'title': j[2]}
		 		if (given): 	scenarios[j[1]]['custom_bdd_given'] = given[0]
		 		if (when): 		scenarios[j[1]]['custom_bdd_when'] = when[0]
		 		if (then): 		scenarios[j[1]]['custom_bdd_then'] = then[0]
		 		if (examples): 	scenarios[j[1]]['custom_bdd_examples'] = examples[0]
		 		if (tags): 		scenarios[j[1]]['custom_bdd_tags'] = tags
                
		 		# Add/Update TestRail testcase
				if scenario_id == None:
			 		scenario_id = self.client.send_post('add_case/' + str(section_id), scenarios[j[1]])['id']
			 		print("Adding new Test Case\t- id: " + str(scenario_id))
				else:
					self.client.send_post('update_case/' + str(scenario_id), scenarios[j[1]])
					print("Updating Test Case\t\t- id: " + str(scenario_id))


class gherkintotestrailimportbasetests(sublime_plugin.TextCommand):

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

		# s = File content
		alltextreg = sublime.Region(0, self.view.size())
		s = self.view.substr(alltextreg).strip()

		suite_name = "Base Test"
		currSuites = self.client.send_get('get_suites/' + str(self.currProject))
		

		# Get Suite ID
		suite_id = None
		for x in currSuites:
			if x['name'] == suite_name:
				suite_id = x['id']
		

		# Check if 'Base Tests' suite exists
		if suite_id == None:
			# Add 'Base Tests' suite
			suite_id = self.client.send_post('add_suite/' + str(self.currProject), {"name": suite_name})['id']
			print("Adding new Test Suite\t- id: " + str(suite_id))
		else:
			# Update 'Base Tests' suite
			print("Updating Test Suite\t\t- id:" + str(suite_id))


		# FeatureFile: Feature name -> Section in 'Base Tests' suite
		featureFile_featureName = re.search(r'Feature: (.*)', s).group(1)

		# Get Sections from TestRails
		smokeTestsSections = self.client.send_get('get_sections/' + str(self.currProject) + '&suite_id=' + str(suite_id))

		# Check if Section exists
		smokeTestsSection_id = None
		for x in smokeTestsSections:
			if x['name'] == featureFile_featureName:
				smokeTestsSection_id = x['id']

		# Add/Update section
		if smokeTestsSection_id == None:
			smokeTestsSection_id = self.client.send_post('add_section/' + str(self.currProject), {"suite_id": suite_id, "name": featureFile_featureName})['id']
			print("Adding new Section\t\t- id: " + str(smokeTestsSection_id))
		else:
			print("Updating Section\t\t- id: " + str(smokeTestsSection_id))


		sections = {}
		scenarios = {}
		

		parsedFeatureFile = re.findall(r'# (.*)\n((?:.*\n)*?\n)\n', s);
		print("DEBUG:	There are " + str(len(parsedFeatureFile)) + " sections in the Feature file.")


		# Parse Feature file by Sections
		for i in parsedFeatureFile:

			print("DEBUG:		Section: " + i[0]);

			# Parse actual Section by Scenarios
		 	for j in re.findall(r'((?:@.*)\n)*Scenario(?: Outline)*: (.*) - (.*)\n((?:.*\n)*?)\n', i[1]):
				
		 		print("DEBUG:			Scenario: " + j[2]);

		 		# j[0] = Tags
		 		# j[1] = Scenario ID
		 		# j[2] = Scenario String
		 		# j[3] = Scenario Content

		 		# Get Scenarios from TestRail
				currScenarios = self.client.send_get('get_cases/' + str(self.currProject) + '&suite_id=' + str(suite_id) + '&section_id=' + str(smokeTestsSection_id))
				scenario_id = None
				for x in currScenarios:
					if x['custom_bdd_id'] == j[1]:
						scenario_id = x['id']

				# Parse actual Scenario by parts
		 		tags 		= j[0]
		 		given 		= re.findall(r'\t*Given ((?:.*)(?:\n\t\t(?:And|But) .*)*)', j[3])
		 		when  		= re.findall(r'\t*When ((?:.*)(?:\n\t\t(?:And|But) .*)*)', j[3])
		 		then 		= re.findall(r'\t*Then ((?:.*)(?:\n\t\t(?:And|But) .*)*)', j[3])
		 		examples 	= re.findall(r'\t*Examples:\n((?:\t*.*\n)*)', j[3])

		 		# Remove whitespace character from the back end from the beginning
		 		tags = tags.strip();
		 		print("DEBUG:				Tags: " + tags);

		 		# Create the Scenario object for TestRail upload
		 		scenarios[j[1]] = {'custom_bdd_id': j[1], 'title': j[2]}
		 		if (given): 	scenarios[j[1]]['custom_bdd_given'] = given[0]
		 		if (when): 		scenarios[j[1]]['custom_bdd_when'] = when[0]
		 		if (then): 		scenarios[j[1]]['custom_bdd_then'] = then[0]
		 		if (examples): 	scenarios[j[1]]['custom_bdd_examples'] = examples[0]
		 		if (tags): 		scenarios[j[1]]['custom_bdd_tags'] = tags

		 		# Work only with Base scenarios
		 		# Add/Update TestRail testcase
				if scenario_id == None:
			 		scenario_id = self.client.send_post('add_case/' + str(smokeTestsSection_id), scenarios[j[1]])['id']
			 		print("DEBUG:					Adding new Test Case\t- id: " + str(scenario_id))
				else:
					self.client.send_post('update_case/' + str(scenario_id), scenarios[j[1]])
					print("DEBUG:					Updating Test Case\t\t- id: " + str(scenario_id))




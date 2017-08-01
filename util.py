#import gerrytests as gt
import json, os
from pprint import pprint

# Map from state number to state abbreviation
STATES = [
	'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA',
	'HI','ID','IL','IN','IA','KS','KY','LA','ME','MD',
	'MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
	'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC',
	'SD','TN','TX','UT','VT','VA','WA','WV','WI','WY'
]

def parse_results(input_filename, output_filename=None, silent=False):
	""" Read a csv file describing district-level election results.

	The following format is expected:
		year, statenumber, districtnumber, result, ?, ?

	Districts are assumed to be listed in numerical order

	Parameters
	----------
	input_filename : str
		Name of results file to read
	output_filename : str, optional
		Name of file in which to save results.  If not provided, return
		value will not be saved to file.
	silent : bool, optional
		Whether to suppress parse errors while reading.  Default is false.

	Returns
	----------
	results : dict
		A structured version of the input file, indexed by year and then state
		postal abbreviation.  For example the line 2012,1,1,0.7 will be added as
		results['2012']['AL'][0] = 0.7

	"""

	# Initialize results dict
	results = {};
	with open(filename) as file:
		for i,line in enumerate(file):
			try:
				#
				(year, state, _, res, _, _) = line.split(',')
			except:
				print('Error reading line %d: %s' % (i, line))
				if silent:
					print('\tignoring')
					continue
				else: raise

			# State Postal code from alphabetical index
			state = STATES[int(state) - 1]

			if state not in results[year]:
				results[year][state] = []
			results[year][state].append(float(res))

	with open('static/data/allresults.json', 'w') as file:
		json.dump(results, file)

	return results

def run_all_tests(all_results, years=None):
	""" Run all of the tests on each of the elections present in results.

	Parameters
	----------
	all_results : dict
		A dictionary indexed by string years of district-level results per state.
		This is the same format output by parse_results.

	years : list, optional

	"""

	impute_val = 0.75

	if years is None:
		years = all_results.keys()

	for year in years:
		year_results = all_results[year]
		print('Running tests for %s' % year)
		# get all national results for current year
		national_results = []
		for state in year_results:
			if year in ['2012', '2014', '2016'] and state in ['MI', 'NC', 'OH', 'PA', 'VA', 'WI']: continue
			national_results += year_results[state]

		for idx, x in enumerate(national_results):
			if x == 1: national_results[idx] = impute_val
			if x == 0: national_results[idx] = 1 - impute_val

		# dict for storing test results
		if year not in tests: tests[year] = {}
		for state, state_results in year_results.items():
			# DO IMPUTATION
			imputed = list(state_results)
			for idx, x in enumerate(state_results):
				if x == 1: imputed[idx] = impute_val
				if x == 0: imputed[idx] = 1 - impute_val

			print('\t- %s' % state)
			# run each test and save outcome
			tests[year][state] = {
				"test1"		: gt.test_lopsided_wins(imputed),
				"test2"		: gt.test_consistent_advantage(imputed),
				"test3"		: gt.test_fantasy_delegations(imputed, national_results, n_sims=1000000),
				"voteshare" : sum(state_results) / len(state_results),
				"seats"		: len([0 for r in state_results if r > 0.5]),
				"results"	: state_results,
				"ndists"	: len(state_results),
				"nall"		: len(all_results),
				"state"		: state,
				"year"		: year
			}

	with open('static/data/precomputed_tests.json', 'w') as file:
		json.dump(tests, file)

	return tests



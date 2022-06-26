import LoadLocationData
from collections import defaultdict
import random
import copy
import time

import RandomizeFunctions


def findAllSilverUnlocks(req, locList, handled=[]):
	#req = "Mt. Silver Outside"
	newFind = []
	findSilverItems = list(filter(lambda x: req in x.LocationReqs, locList))
	for findSilver in findSilverItems:
		if findSilver in handled:
			continue
		handled.append(findSilver)
		if findSilver.Type == "Item":
			newFind.append(findSilver)
		# TODO: Investigate adding Transition as well as fixing warp issues
		elif findSilver.Type == "Map":
			newFinds = findAllSilverUnlocks(findSilver.Name, locList, handled)
			for find in newFinds:
				newFind.append(find)

	return newFind

# Function should be made recurisve
# So if a dead end is somewhere in a chain, it is also removed
def pruneWarpRequirementsTree(requirementsDict, start_element=None, previous_name=None, known=[]):
	toPrune = []
	partial_prunes = []



	if start_element is None:
		for req in requirementsDict.items():
			req_key = req[0]
			newPrune, newPartial = pruneWarpRequirementsTree(requirementsDict, req_key, None, known)

			toPrune.extend(newPrune)

			continue

			# for path in l:
			# 	if len(path) == 1:
			# 		path_element = path[0]
			# 		if path_element.endswith(LoadLocationData.WARP_OPTION):
			# 			confirm = requirementsDict[path_element]
			# 			if len(confirm) == 1:
			# 				confirm_path = confirm[0]
			# 				if len(confirm_path) == 1:
			# 					confirm_element = confirm_path[0]
			# 					if confirm_element == key:
			# 						print("Should prune:", key, path)
			# 						toPrune.append((key, path))
	else:

		if start_element in known:
			return toPrune, partial_prunes

		known.append(start_element)


		if not start_element.endswith(LoadLocationData.WARP_OPTION):
			return toPrune, partial_prunes

		pathsHere = requirementsDict[start_element]

		if len(pathsHere) == 0:
			return toPrune, partial_prunes

		duplicate_check = []
		for path in pathsHere:
			if path == start_element:
				print("to pruneA:", start_element, path)
				toPrune.append((start_element, path))
			elif path not in duplicate_check:
				duplicate_check.append(path)
			else:
				print("to pruneB:", start_element, path)
				toPrune.append((start_element, path))
				toPrune.append((start_element, path))

		path_translation = {}
		index = 0
		for path in duplicate_check:
			skipped = 0
			for element in path:
				if not element.endswith(LoadLocationData.WARP_OPTION):
					pass
				elif element == previous_name:
					skipped += 1
				else:
					newPrunes, newPartialPrunes = pruneWarpRequirementsTree(requirementsDict, element, start_element, known)
					path_translation[index] = (newPrunes, newPartialPrunes)

					# TODO implement recursive cases

			if skipped == len(path):
				partial_prunes.append((start_element, path))

			index += 1

		for p in path_translation.items():
			yes_prune = p[1][0]
			maybe_prune = p[1][1]
			for y in yes_prune:
				if y != []:
					toPrune.append(y)

			for m in maybe_prune:
				print("maybe?", m)








	if start_element is None:
		for prune in toPrune:
			requirementsDict[prune[0]].remove(prune[1])
		return requirementsDict
	else:
		return toPrune, partial_prunes


def RandomizeItems(goalID,locationTree, progressItems, trashItems, badgeData, seed, inputFlags=[], reqBadges = { 'Zephyr Badge', 'Fog Badge', 'Hive Badge', 'Plain Badge', 'Storm Badge', 'Glacier Badge', 'Rising Badge'},
				   coreProgress= ['Surf','Fog Badge', 'Pass', 'S S Ticket', 'Squirtbottle','Cut','Hive Badge'],
				   allPossibleFlags = ['Johto Mode','Kanto Mode'],
				   plandoPlacements = {},
				   dontReplace = []):
	monReqItems = ['ENGINE_POKEDEX','COIN_CASE', 'OLD_ROD', 'GOOD_ROD', 'SUPER_ROD']
	
	random.seed(seed)
	#add the "Ok" flag to the input flags, which is used to handle locations that lose all their restrictions
	inputFlags.append('Ok')
	#build progress set
	progressList = copy.copy(sorted(progressItems))
	progressList.extend(sorted(reqBadges))
	progressSet = copy.copy(sorted(progressList))
	coreProgress = list(sorted(frozenset(coreProgress).intersection(frozenset(progressSet))))
	locList = sorted(LoadLocationData.FlattenLocationTree(locationTree), key= lambda i: ''.join(i.Name).join(i.requirementsNeeded(defaultdict(lambda: False))))
	allocatedList = []

	#define set of badges
	badgeSet = list(sorted(badgeData.keys()))
	#define set of trash badges
	trashBadges = list(sorted(frozenset(badgeData.keys()).difference(frozenset(reqBadges))))
	trashItems.extend(sorted(trashBadges))
	trashItems.sort()
	#stores current requirements for each location
	requirementsDict = defaultdict(lambda: [])

	MtSilverSubItems = findAllSilverUnlocks("Mt. Silver Outside",locList)
	Route28SubItems = findAllSilverUnlocks("Route 28", locList)

	MtSilverSubItems.extend(Route28SubItems)


#shuffle the lists (no seriously, this is a perfectly valid randomization strategy)
	#random.shuffle(locList)
	#random.shuffle(progressList)
	#random.shuffle(coreProgress)
	#random.shuffle(trashItems)
	locList = random.sample(locList, k=len(locList))
	progressList = random.sample(progressList, k=len(progressList))
	coreProgress = random.sample(coreProgress, k=len(coreProgress))
	trashItems = random.sample(trashItems, k=len(trashItems))

	#build spoiler
	spoiler = {}
	#print('Building mappings')
	#note: these are the randomizer only flags, they do not map to actual logic defined in the config files
	#flagList = ['Rocket Invasion', '8 Badges', 'All Badges']
	flagList = ['Assumed Fill', 'All Badges', 'Ok','External Checking']
	if(len(plandoPlacements) > 0):
		flagList.append('External Checking')
	#build the initial requirements mappings
	allReqsList = copy.copy(progressSet)
	itemCount = 0
	single_flags_set = []
	flags_with_path = []

	for i in locList:
		#baseline requirements
		#allReqs = i.LocationReqs+i.FlagReqs+i.itemReqs
		allReqs = sorted(i.requirementsNeeded(defaultdict(lambda: False)))
		allReqsList.extend(allReqs) 
		allReqsList.append(i.Name)
		requirementsDict[i.Name].append(allReqs)
		for j in sorted(i.FlagsSet):
			requirementsDict[j].append(allReqs)
			flagList.append(j)
			if j in flags_with_path:
				pass
			elif j in single_flags_set:
				single_flags_set.remove(j)
				flags_with_path.append(j)
			else:
				single_flags_set.append(j)

		if i.Type == 'Item':
			itemCount = itemCount+1


	# If Warps enabled, prune the requirements tree
	# This would be to remove issues with large locations
	# For example, Goldenrod Store has many access points
	# The iteration here will pick a random path
	# If a dead-end, it will fail immediately as only route to if from there

	#if "Warps" in inputFlags:
		#pruneWarpRequirementsTree(requirementsDict)


	# Store flags set in a single location and forcibly update
	# All instances of that flag with its requirements
	# To resolve a placement issue
	# e.g. Dragons Den Entrance requiring Strength due to flag changes

	# However, working out the way to do this is complex
	# Especially as those location requirements would also need updating
	# Is there a better way to do this?

	#for flag in single_flags_set:
		#affected = list(filter(lambda x: flag in x,requirementsDict.iteritems()))
		# do updating
	#	pass


	#print('Total number of items: '+str(itemCount))
	E4Badges = random.sample(badgeSet,8)
	#print('E4Badges')
	#print(E4Badges)
	#choose 8 random badges and make them the "required" badges to access the elite 4
	#this is needed to break the randomizer's addiction to E4 required seeds on extreme
	if 'Sane Extreme E4 Access' in inputFlags:
		for i in requirementsDict['8 Badges']:
			i.extend(E4Badges)
	#if we are in plando mode (explicit placements, only use explicit checks for locations which have the option)
	if(len(plandoPlacements)>0):
		for i in requirementsDict:
			explicitable = False
			explicitOption = None
			for j in requirementsDict[i]:
				if('Explicit Checking' in j):
					explicitable = True
					explicitOption = j
			if explicitable:
				#print(requirementsDict[i])
				requirementsDict[i] = [explicitOption]
				#print(requirementsDict[i])

	#extract all core items out and put them in shuffled order at the start (which is the BACK) of the item list
	#this is done because these items unlock way too many item locations, so we want to maximize their legal locations
	for i in coreProgress:
		progressList.remove(i)
	progressList = progressList+coreProgress


	if 'Allocate Badges First' in inputFlags:
		addEnd = []
		for i in progressList:
			if 'Badge' in i:
				addEnd.append(i)
		for i in addEnd:
			progressList.remove(i)
			progressList.append(i)


				
	#put surf at the front of the list because with badges being shuffled, there is otherwise an abnormal bias towards early surf
	progressList.remove('Surf')
	progressList.append('Surf')
	#print(progressList)

	if "Fly Warps" in inputFlags:
		progressList.remove('Fly')
		progressList.remove('Storm Badge')
		progressList.append('Storm Badge')
		progressList.append('Fly')

	
	#go through all the plandomizer allocations and try to put them in locations specified (generated seed will ATTEMPT to obey these)
	#this works by putting the plando placements to be tried first
	for i in plandoPlacements:
		if (plandoPlacements[i] in progressList):
			for j in range(0, len(locList)):
				if(locList[j].Name == i):
					locInd = j
					#print(j)
			#print(locList[0].Name)
			locList.insert(0, locList.pop(locInd))
			#print(locList[0].Name)
			progressList.remove(plandoPlacements[i])
			progressList.insert(len(progressList),plandoPlacements[i])
	#print(plandoPlacements)
	#print(progressList)
	#keep copy of initial requirements dictionary to check tautologies
	initReqDict = copy.copy(requirementsDict)
	usedFlagsList = list(sorted(frozenset(allReqsList).intersection(allPossibleFlags)))
	#begin assumed fill loop
	valid = True
	# while(len(progressList)>0 and valid):
		#pick an item to place
		# toAllocate = progressList.pop()
		# #print('Allocating '+toAllocate)
		# if toAllocate in progressItems:
			# allocationType = 'Item'
		# else:
			# allocationType = 'Gym'
		#iterate through randomly ordered locations until a feasible location to place item is found
	maxIter = len(progressList)
	#progressList.reverse()
	#print(progressList)
	previousCount = 0
	while len(progressList) > 0 and maxIter > 0:

		#print("iter=",maxIter, "pl:", len(progressList), progressList)

		if previousCount == len(progressList):
			remainingLocations = list(filter(lambda x: x.Type == "Item" or x.Type == "Gym", locList))
			for r in remainingLocations:
				print("r=",r.Name)

		previousCount = len(progressList)

		maxIter = maxIter - 1
		valid = False
		iter = 0
		retryPasses = 4

		#determine type of location to allocate based of progress list
		allocationType = 'Item'
		#if progressList[-1] in progressItems:
		#	allocationType = 'Item'
		#else:
		#	allocationType = 'Gym'
		#	toAllocate = progressList[-1] #If its a badge, we always force the allocation of THAT badge

		#LocationList = list(filter(lambda x: x.Type != "Map" and x.Type != "Transition"), locList)

		while not valid and iter < len(locList) and retryPasses > 0 and len(progressList) > 0:
			#sub item allocation loop, so that locations are at least randomly given items they can actually have
			allocated = False
			nLeft = len(progressList)
			while nLeft > 0 and not allocated:
				#if its a plando placement, just place it, we'll complain if infeasible later on
				# TODO Investigate this functionality, as seems to want 'Name' appended
				if locList[iter] in plandoPlacements:
					toAllocate = plandoPlacements[locList[iter]]
					nLeft = 0
					placeable = True
				else:
					#skip over entries until we get to the type we're trying to allocate
					placeable = False
					while not placeable and nLeft > 0 and allocationType != 'Gym':
						nLeft = nLeft - 1
						toAllocate = progressList[nLeft]
						if allocationType == 'Item' and toAllocate in progressList:
							placeable = True
						# if allocationType == 'Gym' and not (toAllocate in progressItems):
							# placeable = True
					#print('Allocating '+toAllocate)
					if allocationType == 'Gym':
						placeable = True
						nLeft = 0
				legal = True
				illegalReason = None
				#don't attempt to put badges in mt. silver
				#if('Mt. Silver' in locList[iter].LocationReqs and toAllocate in badgeSet and not 'Open Mt. Silver' in inputFlags):
				#	placeable = False

				if (locList[iter] in MtSilverSubItems and toAllocate in badgeSet and not 'Open Mt. Silver' in inputFlags):
					placeable = False

				if (locList[iter] in MtSilverSubItems and toAllocate in coreProgress):
					placeable = False

				if locList[iter].isShop() and \
						(toAllocate in badgeSet or toAllocate in \
					[ "Pokegear", "Expansion Card", "Radio Card", "ENGINE_POKEDEX" ]):
					# Shopsanity does not yet support flags in shops
					placeable = False

				# Unlikely to be the culprit?
				if locList[iter].Type == "Map" or locList[iter].Type == "Transition":
					break

				warpImpossibleCheck = requirementsDict[locList[iter].Name]
				impossible_paths = 0
				for path in warpImpossibleCheck:
					path_is_impossible = ("Impossible" in path) or ("Unreachable" in path) or ("Banned" in path)
					if path_is_impossible:
						impossible_paths +=1

				if impossible_paths > 0 and impossible_paths >= len(warpImpossibleCheck):
					#print("Impossible:", locList[iter].Name + ' cannot contain ' + toAllocate)
					break


				#is it the right type of location?
				##print(locList[iter].Name)
				##print(locList[iter].Type)
				#all locations are now the same!
				if((locList[iter].Type == 'Item' or locList[iter].Type == 'Gym') and placeable):
					#print('Trying '+locList[iter].Name +' as ' +toAllocate)
					#do any of its dependencies depend on this item/badge?
					randOpt = random.choice(range(0,len(requirementsDict[locList[iter].Name])))
					allDepsList = sorted(copy.copy(requirementsDict[locList[iter].Name][randOpt]))
					oldDepsList = []
					newDeps = allDepsList
					addedList = [locList[iter].Name]
					revReqDict = defaultdict(lambda: [])
					while oldDepsList != allDepsList and legal:
						oldDepsList = allDepsList
						for j in newDeps:
							# Break out before continuing if item is locked to Red due to modifiers
							if "Red" in newDeps:
								#illegalReason = "Red"
								legal = False
								break

							if not legal:
								break

							jReqs = []
							if(len(requirementsDict[j])>0):
								#print('Choosing non-tautological path for '+j)
								#choose a random path through dependencies that IS NOT A TAUTOLOGY!

								# If a path has no requirements, choose this one as means always available
								# Similarly, if a path only contains 'Warps'
								# Otherwise X% chance of failure on each run through



								paths = copy.copy(requirementsDict[j])
								random.shuffle(paths)

								defaultPath = None
								for check in paths:
									if len(check) == 0:
										defaultPath = check
									# If Warps option enabled, always pick this one!
									elif len(check) == 1 and check[0] in inputFlags:
										defaultPath = check

								#pick an option from paths which isn't a tautology!
								tautologyCheck = True

								tautIter = 0
								#only need to pick if there are two options!
								if(len(requirementsDict[j])>1):

									# better strategy, if you choose option A from the multiple options, then the locations required by A CANNOT require j!
									# so when choosing a path to the locations required by A, we CANNOT choose an option with j as a dependency!
									# also, we don't pick paths that require the item we're trying to allocate, for obvious reasons
									trueOption = defaultPath

									if trueOption is None:
										for k in paths:
											#print('trying potential path:')
											#print(k)

											# Tiny optimisation, break out of path if contains the item to be allocated in the path
											# Previously, continued through each step in the path requirements
											if toAllocate in k:
												continue

											kTrue = True

											for l in k:
												# Warps add edge case where warps can lead to themselves!
												kTrue = kTrue and (l != j)
												#print("Check element l in k", l)
												#kTrue = not (len(requirementsDict[l]) == 1 and j in requirementsDict[l][0])
												#if not kTrue:
												#	print("Debug: A")
												kTrue = kTrue and (l not in revReqDict[j])
												#if not kTrue:
												#	print("Debug: B")
												lTrueOr = len(requirementsDict[l]) == 0
												for m in requirementsDict[l]:
													lTrueOr = lTrueOr or toAllocate not in m
												kTrue = kTrue and lTrueOr
												#if not kTrue:
												#	print("Debug: C")
												#also make sure the location doesn't literally require it
												kTrue = kTrue and l != toAllocate
												#if not kTrue:
												#	print("Debug: D")
												#also make sure its not impossible
												kTrue = kTrue and l != 'Impossible' and l != "Banned" and l != "Unreachable"
												#if not kTrue:
												#	print("Debug: E")
												#also make sure the requirements aren't impossible (accounts for multi-entrances, which can never be impossible)
												if(len(requirementsDict[l]) != 0):
													kTrue = kTrue and not ('Impossible' in requirementsDict[l][0] or\
																		   'Banned' in requirementsDict[l][0] or\
																		   'Unreachable' in requirementsDict[l][0])
												#	if not kTrue:
												#		print("Debug: F")
												if not lTrueOr:
													1+1
													#print('False because '+l+' requires:')
													#print(requirementsDict[l])
												#if a flag we don't have is needed, we can't use that path
												kTrue = kTrue and not (l in usedFlagsList and l not in inputFlags)

												# Warps are bi-directional, so add clause here to prevent automatic tautology
												#if l.endswith(LoadLocationData.WARP_OPTION):
												#	kTrue = kTrue and (l not in allDepsList)


												#if not kTrue:
												#	print("Debug: G")
												if (l in usedFlagsList and l not in inputFlags):
													1+1
													#print('False because the needed flag '+ l +' is not set')
													#print(usedFlagsList)
													#print(inputFlags)
											# If all requirements have already been found, then the potential path is forbidden
											# As it may require cyclic access, especially with warp logic
											# e.g. Ledges only being accessible by warps, but using vanilla within dungeons
											#if len(l) > 0 and len(k) == reqInCurrent:
											#	kTrue = False
											if(kTrue):
												trueOption = k
												#print('found non-tautological path')
												#print(k)
												break
											else:
												1+1
												#print('Path is false')
									#if new choice is none, ignore it because this is a true tautology
									#e.g. trying to place the squirtbottle at the sudowoodo junction
									if(not trueOption is None):
										#add all reverse dependencies onto new choice
										for k in trueOption:
											revReqDict[k].extend(sorted(revReqDict[j]))
											revReqDict[k].append(j)
										jReqs = trueOption
										if j not in addedList:
											addedList.append(j)
										if len(paths)>1:
											1+1
											#print(revReqDict)
									else:
										legal = False
										illegalReason = allDepsList.copy()
										#this is not a legal item location! because it involves a tautology!
										#print('Illegal tautology:')
										#print(paths)
										#print('The following could create the tautology when allocating '+ toAllocate +' to '+locList[iter].Name+':')
										#print(revReqDict[j])
								else:
									jReqs = sorted(requirementsDict[j][0])

									# Due to some behaviour with Warps, need this requirements check
									# Even with a single path as could be randomised
									# Into a tautology (potentially at a previous path)

									if len(paths) > 0:
										singleTrue = True
										for l in paths[0]:
											singleTrue = singleTrue and (l != j)
											singleTrue = singleTrue and (l not in revReqDict[j])
											lTrueOr = len(requirementsDict[l]) == 0
											for m in requirementsDict[l]:
												lTrueOr = lTrueOr or toAllocate not in m
											singleTrue = singleTrue and lTrueOr
											singleTrue = singleTrue and l != toAllocate

											singleTrue = singleTrue and l != 'Impossible' and l != "Banned" and l != "Unreachable"
											if (len(requirementsDict[l]) != 0):
												singleTrue = singleTrue and not ('Impossible' in requirementsDict[l][0] or \
																	   'Banned' in requirementsDict[l][0] or \
																	   'Unreachable' in requirementsDict[l][0])

											if not lTrueOr:
												1 + 1

											singleTrue = singleTrue and not (l in usedFlagsList and l not in inputFlags)

										if not singleTrue:
											legal = False
										else:
											for l in paths[0]:
												revReqDict[l].extend(sorted(revReqDict[j]))
												revReqDict[l].append(j)
									else:
										if 'Impossible' in jReqs or "Banned" in jReqs or "Unreachable" in jReqs:
											legal = False
									if j not in addedList:
										addedList.append(j)
							for k in jReqs:
								if k not in allDepsList:
									newDeps.append(k)

						allDepsList.extend(newDeps)
						#print("New dependencies:", allDepsList)

						#print('Expanded dependencies of '+locList[iter].Name+' to:')
						#print(allDepsList)
						newDeps = []
					#if a dependency requires an input flag (not set by a location, a location, or a progress item), that flag MUST be set
					#print(allDepsList)
					#print(legal)
					#print(frozenset(allDepsList).intersection(frozenset(usedFlagsList)).issubset(inputFlags))
					#print(usedFlagsList)
					#print(frozenset(allDepsList).intersection(set(usedFlagsList)))
					legal = legal and frozenset(allDepsList).intersection(frozenset(usedFlagsList)).issubset(inputFlags)
					if(not frozenset(allDepsList).intersection(frozenset(usedFlagsList)).issubset(inputFlags)):
						1+1
						#print(locList[iter].Name + ' is not legal because it needs flags that are not set')
						#print(set(allDepsList).intersection(set(usedFlagsList)))
					#Impossible locations are illegal
					if("Impossible" in allDepsList or "Banned" in jReqs or "Unreachable" in jReqs):
						illegalReason = "Impossible 2"
						legal = False
					if(toAllocate not in allDepsList and legal or (toAllocate in plandoPlacements.values() and 'unsafePlando' in inputFlags)):
						loc = locList.pop(iter)
						valid = True
						#print('Gave '+ toAllocate +' to '+ loc.Name)
						progressList.remove(toAllocate)
						allocated = True
						#if(loc.isItem()):
						loc.item = toAllocate
						loc.IsGym = False
						loc.IsItem = True
						#print("Spoilers:", loc.Name, loc.item)
						spoiler[loc.item] = loc.Name
						#if(loc.isGym()):
						#	loc.badge = badgeData[toAllocate]
						#	badgeSet.remove(toAllocate)
						#	spoiler[loc.badge.Name] = loc.Name
						allocatedList.append(loc)
						#requirementsDict[toAllocate] = requirementsDict[loc.Name]
						if not 'unsafePlando' in inputFlags:
							requirementsDict[toAllocate] = [list(frozenset(allDepsList))]
						#print(spoiler)
					else:
						#print(locList[iter].Name+' cannot contain '+toAllocate)
						if(toAllocate in allDepsList):
							1+1
							#print('...because it requires '+toAllocate+' to be reached in the first place!')
							#print(spoiler)
						else:
							1+1
							#print('...because its currently an illegal location')
							#print(spoiler)
						#iter = iter+1
				# else:
					# iter = iter+1
				# if iter == len(locList) and not valid:
					# iter = 0
					# retryPasses = retryPasses-1
					# #print('retrying with different paths')
			iter = iter + 1

	#print('----')

	# This should be moved to prevent it running on each attempt through!
	if "RandomiseItems" in inputFlags:
		handles = list(filter(lambda x: len(x.Handles) > 0, locList))
		for handle in handles:
			if "ImpossibleRandomise" in handle.Handles and "Banned" in handle.FlagReqs:
				specialFlagName = handle.Name
				toHandle = list(filter(lambda x: specialFlagName in x.FlagReqs, locList))
				for h in toHandle:
					h.FlagReqs.append("ImpossibleRandomise")

	if "RandomiseItems" in inputFlags:
		item_processor = RandomizeFunctions.RandomItemProcessor(dontReplace)
	else:
		item_processor = None



	#traverse seed to both confirm beatability, allocate "trash" items and determine location distances
	#define the set of active initial locations to consider
	rodList = ['OLD_ROD','GOOD_ROD','SUPER_ROD']
	#overwrite rods into semi-progressive order
	if('SemiProgressiveRods' in inputFlags):
		#print(trashItems)
		for i in range(0,len(trashItems)):
			if('ROD' in trashItems[i]):
				trashItems[i] = rodList.pop()
		#print('---')
		#print(trashItems)

	# Due to changes to items, such as becoming items from banlist, do deep copy?
	activeLoc = copy.deepcopy(locationTree)
	goalReached = False
	randomizerFailed = False
	#Initially we have no badges
	nBadges = 0
	#define the dict of currently accesible locations
	reachable = {}

	#define max distance of each badge
	maxBadgeDist = 0
	state = defaultdict(lambda: False)
	#set initial flags
	for i in inputFlags:
		if i == "Replace Bike":
			state["Bicycle"] = True
		state[i] = True
	#if unsafe plando, put everything from the plando in
	if 'unsafePlando' in inputFlags:
		for i in plandoPlacements:
			state[plandoPlacements[i]] = True
	state['Item Badge Shuffle'] = True
	#define mapping of state to distances at which parts of state were met
	stateDist = defaultdict(lambda: 0)
	stuckCount = 0
	trashSpoiler = {}
	stage = 0

	addAfter = []
	randomizedExtra = {}

	allocatedCount = 0

	while not goalReached and not randomizerFailed:
		stage += 1
		#track if we're stuck
		stuck = True
		#shuffle the list of active locations to prevent any possible biases	
		random.shuffle(activeLoc)
		for i in activeLoc:
			#can we get to this location?
			if(i.isReachable(state) and i.Name not in reachable):

				#print("reachable:",i.Name, "@", stage)
				#if we can get somewhere, we aren't stuck
				stuck = False
				#we can get somehwhere, so set this location in the state as true
				state[i.Name] = True
				#Add sublocations to the set of active locations
				activeLoc.extend(i.Sublocations)
				#set this location as reachable
				reachable[i.Name] = i
				activeLoc.remove(i)
				#set distance of this location
				maxdist = max([stateDist[x] for x in i.requirementsNeeded(defaultdict(lambda: False))],default = 0)
				if i.HasPKMN:
					maxdist = maxdist+1
				i.distance = maxdist
				#set distance of location
				stateDist[i.Name] = i.distance
				#set all relevant flags this location sets
				for j in i.getFlagList():
					state[j] = True
					stateDist[j] = i.distance
				#perform appropriate behaviors for location
				#if its an item, put an item in it
				#double checks items to write due to bizzare bug observed only once
				if(i.isItem() or i.isGym()):
					allocatedCount += 1
					#print("IsReplace", i.Name)
					if(not i.Name in spoiler.values()):
						if i.Name in plandoPlacements:
							item = plandoPlacements[i.Name]
							i.item = item
							print("Plando", i.Name, i.item)
							try:
								trashItems.remove(item)
							except ValueError:
								pass
						else:
							try:
								placeItem = trashItems.pop()
							except Exception as e:
								print("exception",e)
								i.item = "GOLD_LEAF"
								addAfter.append(i)
							while placeItem in monReqItems and 'Mon Locked Checks' in i.requirementsNeeded(defaultdict(lambda: False)):
								oldItem = placeItem
								placeItem = trashItems.pop()
								trashItems.insert(random.randint(0, len(trashItems)), oldItem)

							while placeItem in [ "Pokegear", "Expansion Card", "Radio Card", "ENGINE_POKEDEX", "OLD_ROD", "GOOD_ROD", "SUPER_ROD" ] and \
									i.isShop():
								oldItem = placeItem
								placeItem = trashItems.pop()
								trashItems.insert(random.randint(0, len(trashItems)), oldItem)

							i.item = placeItem
						#print("Trash", i.Name, i.item)
						if i.item != "GOLD_LEAF":
							trashSpoiler[i.Name] = i.item
							i.IsGym = False
							i.IsItem = True

							if i.item == "WATER_STONE" or i.item == "ESCAPE_ROPE":
								state[i.item.replace("_"," ").title()] = True
							# Do this to ensure items are all overwritable with other requirements
							# Even if the item is trash
							elif i.item == "Red Scale" or i.item == "Mystery Egg" or i.item == "Rainbow Wing" or\
								i.item == "COIN_CASE" or i.item == "BLUE_CARD" or i.item == "ITEMFINDER":
									state[i.item] = True


					else:
						state[i.item] = True
						stateDist[i.item] = max(stateDist[i.item],stateDist[i.Name])
						i.item = next(key for key, value in spoiler.items() if value == i.Name)
						i.IsGym = False
						i.IsItem = True
						#print('Progress item '+i.item +' in '+i.Name)
					if(i.item in badgeSet):
						maxBadgeDist = max(maxBadgeDist,i.distance)
						nBadges = nBadges+1
						#print("Not Trash", i.Name, i.item)
						spoiler[i.item] = i.Name
						# if(i.badge is None):
							# i.badge = badgeData[trashBadges.pop()]
						# else:
							# state[i.badge.Name] = True
							# stateDist[i.badge.Name] = max(stateDist[i.badge.Name],stateDist[i.Name])
						#set badge count based flags
						if(nBadges == 7):
							state['Rocket Invasion'] = True
							stateDist['Rocket Invasion'] = maxBadgeDist
						if(nBadges == 8):
							state['8 Badges'] = True
							stateDist['8 Badges'] = maxBadgeDist
						if(nBadges == 16):
							state['All Badges'] = True
							stateDist['All Badges'] = maxBadgeDist
				elif "RandomiseItems" in inputFlags and i.Banned and \
						(i.wasItem() or i.isItem()) \
						and "Impossible" not in i.FlagReqs:
					i.item = item_processor.GetRandomItem(i.NormalItem)
					addAfter.append(i)

			elif "Warps" in inputFlags and "Unreachable" in i.FlagReqs and i.Name not in reachable and i not in addAfter:
				if i.isItem() or i.isGym() or i.wasItem():
					i.item = "BRICK_PIECE"
					addAfter.append(i)
				else:
					activeLoc.extend(i.Sublocations)
			elif "ImpossibleRandomise" in i.FlagReqs\
				and i.Name not in reachable and i not in addAfter and \
				"Impossible" not in i.FlagReqs:
				if (i.isItem() or i.isGym() or i.wasItem()):
					i.item = item_processor.GetRandomItem(i.NormalItem)
					addAfter.append(i)
				else:
					activeLoc.extend(i.Sublocations)

		if(stuckCount == 4):
			randomizerFailed = True
			for j in activeLoc:
				if(not state[j.Name]):
					1+1
					#print('Stuck on '+j.Name+', which needs:')
					#print(j.requirementsNeeded(state))
			#print(state)
		#check if we've become stuck
		if(stuck):
			stuckCount = stuckCount+1
		else:
			stuckCount = 0

	#verify that plando is matched if in use
	for i in plandoPlacements:
		if(plandoPlacements[i] in spoiler and spoiler[plandoPlacements[i]] != i):
			#raise Exception('Did not match plando placements!!!', plandoPlacements[i], i, spoiler[plandoPlacements[i]],)
			raise Exception('Did not match plando placements!!!')

	for item in addAfter:
		if item.wasItem() or item.isItem() or item.isGym():
			item.IsItem = True
			item.Type = 'Item'
			reachable[item.Name] = item
			randomizedExtra[item.Name] = item.item

	# TODO: Handle any items deemed not possible to reach even after all remaining processing
	# Preferably all to one item to make this obvious to find/identify bugs

	remainingItems = True
	# If RandomiseItems is off, these items will instead be vanilla
	while "RandomiseItems" in inputFlags and remainingItems:
		remainingItems = False
		for i in activeLoc:
			if i.Name not in reachable and (i.isItem() or i.isGym() or i.wasItem()) \
					and "Impossible" not in i.FlagReqs: # Impossible means NEVER overwrite
														# e.g. Not randomising Pokegear
				remainingItems = True
				activeLoc.extend(i.Sublocations)
				i.item = "SILVER_LEAF"
				i.IsItem = True
				i.Type = "Item"
				reachable[i.Name] = i
				randomizedExtra[i.Name] = i.item
				print(i.Name,"now","Silver Leaf")



	#Activate delete fly if needed
	if('Delete Fly' in inputFlags):
		for i in reachable.values():
			if i.isItem():
				#print(i.Name)
				#print('item is: '+str(i.item))
				if i.item == 'Fly':
					#print('deleted fly')
					i.item = 'BERRY'

	changes = RandomizeFunctions.HandleItemReplacement(reachable,inputFlags)

	for change in changes.keys():
		if change in trashSpoiler:
			trashSpoiler[change] = trashSpoiler[change] + "->" + changes[change]
		if change in randomizedExtra:
			randomizedExtra[change] = randomizedExtra[change] + "->" + changes[change]

	#if len(trashItems) > 0 and not randomizerFailed:
		#print(len(trashItems), trashItems)

	#print(stateDist)
	#print(spoiler)
	#print(nBadges)
	#print('illegal')
	#print('remaining')
	#print(trashItems)
	#print('Total number of checks in use: '+str(len(spoiler)+len(trashSpoiler)))
	return (reachable, spoiler, stateDist, randomizerFailed, trashSpoiler, requirementsDict, progressList, locList, randomizedExtra)
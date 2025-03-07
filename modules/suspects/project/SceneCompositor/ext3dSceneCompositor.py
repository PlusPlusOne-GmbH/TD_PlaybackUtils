
'''Info Header Start
Name : ext3dSceneCompositor
Author : Wieland@AMB-ZEPH15
Saveorigin : Project.toe
Saveversion : 2023.11880
Info Header End'''

from typing import Union

class ext3dSceneCompositor:
	"""
	ext3dSceneCompositor description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		self.tweener = self.ownerComp.op("tweenerDependency").GetGlobalComponent()

	def _items(self):
		return { child for child in self.ownerComp.op("itemRepo").Repo.findChildren( depth = 1, parName = "Level Progress")}


	def _activeItems(self):
		return { child for child in self._items() if child.par.Level.eval() }

	def _sceneItems(self, name):
		sceneTable = self.ownerComp.op("sceneRepo").Repo.op(name)
		rows = sceneTable.rows() if sceneTable is not None else []
		return { self.ownerComp.op("itemRepo").Repo.op(row[0]) for row in rows }

	def _fadeLevel(self, operator, target:float, time:float):
		self.tweener.RelativeTween(
			operator.par.Level, 
			target,
			1 / max( time, 1 / project.cookRate )
		)

	def _fadeProgress(self, operator, target:float, time:float):
		self.tweener.RelativeTween(
			operator.par.Progress, 
			target,
			1 / max( time, 1 / project.cookRate )
		)


	def _presetFade(self, itemOP, sceneName, time):
		presetManager 	= itemOP.op("_presetManager")
		if presetManager is None: return False
		return presetManager.Recall_Preset(sceneName, time)


	def SetItem(self, item:COMP, state:bool, time = 1, presetName = ""):
		if not item.par.State.eval(): item.par.Progress.val = 0
		self._fadeLevel( item, float(state), time )
		self._fadeProgress( item, 1+float(not state), item)

	def SetItems(self, sceneItems, time, presetNames = []):

		activeItems 	= self._activeItems()
		fadeOutItems 	= activeItems - sceneItems
		fadeInItems 	= sceneItems - activeItems
		transitionItems = activeItems - fadeOutItems - fadeInItems
		self.ownerComp.op("callbackManager").Do_Callback(
			"onRecall", fadeInItems, fadeOutItems, transitionItems, time, self.ownerComp
		)
		for transitionItem in transitionItems:
			for presetName in presetNames:
				self._presetFade(transitionItem, presetName , time)

		for fadeOutItem in fadeOutItems:
			fadeTime = time if fadeOutItem.par.Customouttime.eval() < 0 else fadeOutItem.par.Customouttime.eval()
			self._fadeLevel( fadeOutItem, 0, fadeTime )
			self._fadeProgress( fadeOutItem, 2, fadeTime)

		for fadeInItem in fadeInItems:
			fadeTime = time if fadeInItem.par.Customintime.eval() < 0 else fadeInItem.par.Customintime.eval()
			
			for presetName in presetNames:
				( 	self._presetFade(
						fadeInItem, f"_pre_{presetName}" , 0
					) and self._presetFade(
						fadeInItem, f"{presetName}" , fadeTime
					) 
				) or self._presetFade(
					fadeInItem, f"{presetName}" , 0
				)
			fadeInItem.par.Progress.val = 0
			self._fadeProgress( fadeInItem, 1, fadeTime)
			self._fadeLevel( fadeInItem, 1, fadeTime)

		return fadeInItems, transitionItems, fadeOutItems

	def Take(self, sceneNames:Union[str, list], time:float):
		sceneItems = set()

		if not isinstance( sceneNames, list): sceneNames = [ sceneNames ]

		sceneItems = sceneItems.union(*[
				self._sceneItems( _name ) for _name in sceneNames
			])
		
		if not sceneItems: sceneItems = self._sceneItems( ["_Default"] )

		return self.SetItems( sceneItems, time, presetNames = sceneNames )


	def RecordNewScene(self, name, recordPreset = True):
		_name = tdu.validName( name )
		sceneTable = self.ownerComp.op("sceneRepo").Repo.op(_name) or self.ownerComp.op("sceneRepo").Repo.create(tableDAT, _name)
		sceneTable.clear()
		
		sceneTable.appendCol([
			item.name for item in self._activeItems()
		])

		if recordPreset:
			for sceneItem in self._activeItems():
				presetManager = sceneItem.op("_presetManager")
				if presetManager is None: continue
				presetManager.Store_Preset( _name )
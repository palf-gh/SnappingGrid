# encoding: utf-8
from __future__ import division, print_function, unicode_literals
import objc
import traceback
import os
import math
from GlyphsApp import Glyphs, EDIT_MENU, VIEW_MENU, DRAWBACKGROUND, MOUSEDRAGGED, MOUSEUP, OFFCURVE
from GlyphsApp.plugins import GeneralPlugin
from AppKit import (
	NSMenuItem, NSColor, NSBezierPath, NSPoint,
	NSTextField, NSStepper, NSButton, NSColorWell,
	NSBundle, NSNib,
	NSAttributedString, NSFont, NSForegroundColorAttributeName, NSFontAttributeName,
	NSApp,
)
from Foundation import NSObject, NSSelectorFromString

PREF = 'com.palf.SnappingGrid'

class SettingsPanelController(NSObject):
	panel           = objc.IBOutlet()
	_labelGridMode  = objc.IBOutlet()
	_radioDivision  = objc.IBOutlet()
	_radioUnit      = objc.IBOutlet()
	_labelMainGrid  = objc.IBOutlet()
	_captionMainV   = objc.IBOutlet()
	_captionSubV    = objc.IBOutlet()
	_mainH          = objc.IBOutlet()
	_mainV          = objc.IBOutlet()
	_mainHStep      = objc.IBOutlet()
	_mainVStep      = objc.IBOutlet()
	_mainSync       = objc.IBOutlet()
	_labelSubGrid   = objc.IBOutlet()
	_subH           = objc.IBOutlet()
	_subV           = objc.IBOutlet()
	_subHStep       = objc.IBOutlet()
	_subVStep       = objc.IBOutlet()
	_subSync        = objc.IBOutlet()
	_labelMainColor = objc.IBOutlet()
	_mainColorWell  = objc.IBOutlet()
	_labelSubColor  = objc.IBOutlet()
	_subColorWell   = objc.IBOutlet()
	_snapCheck       = objc.IBOutlet()
	_cancelButton    = objc.IBOutlet()
	_okButton        = objc.IBOutlet()
	_labelGridShape  = objc.IBOutlet()
	_radioSquare     = objc.IBOutlet()
	_radioTriangle   = objc.IBOutlet()
	_labelOrientation = objc.IBOutlet()
	_radioHorizontal = objc.IBOutlet()
	_radioVertical   = objc.IBOutlet()
	_resetButton     = objc.IBOutlet()

	def initWithPlugin_(self, plugin):
		self = objc.super(SettingsPanelController, self).init()
		if self is None:
			return None
		self.plugin = plugin
		self._isUpdatingControls = False
		self._stepperPairs = ()
		return self

	def show(self):
		if self.panel is None:
			self._loadNib()
		self._loadToUI()
		self.panel.makeKeyAndOrderFront_(None)

	def _loadNib(self):
		plugin_file = None
		try:
			plugin_file = self.plugin.__file__()
		except Exception:
			plugin_file = __file__
		resource_root = os.path.expanduser(os.path.dirname(os.path.abspath(plugin_file)))
		nib_path = os.path.join(resource_root, 'SnappingGridSettings.nib')
		from Foundation import NSURL
		nib_url = NSURL.fileURLWithPath_(nib_path)
		nib = NSNib.alloc().initWithContentsOfURL_(nib_url)
		if nib is None:
			raise RuntimeError('Could not create NSNib from %s' % nib_path)
		self._topLevelObjects = None
		ok, objects = nib.instantiateWithOwner_topLevelObjects_(self, None)
		if ok:
			self._topLevelObjects = objects
		if not ok or self.panel is None:
			raise RuntimeError('Failed to instantiate SnappingGridSettings.nib (ok=%s, panel=%s)' % (ok, self.panel))
		self._wireControls()
		self._applyLocalisation()
		self.panel.center()

	def _wireControls(self):
		step_action = NSSelectorFromString('stepperChanged:')
		for step in (self._mainHStep, self._mainVStep, self._subHStep, self._subVStep):
			step.setMinValue_(1)
			step.setMaxValue_(999)
			step.setIncrement_(1)
			step.setValueWraps_(False)
			step.setTarget_(self)
			step.setAction_(step_action)
		for field in (self._mainH, self._mainV, self._subH, self._subV):
			field.setEditable_(True)
			field.setSelectable_(True)
			field.setBezeled_(True)
			field.setDrawsBackground_(True)
			field.setDelegate_(self)
		self._stepperPairs = (
			(self._mainHStep, self._mainH),
			(self._mainVStep, self._mainV),
			(self._subHStep, self._subH),
			(self._subVStep, self._subV),
		)
		mode_sel = NSSelectorFromString('modeChanged:')
		self._radioDivision.setTarget_(self)
		self._radioDivision.setAction_(mode_sel)
		self._radioUnit.setTarget_(self)
		self._radioUnit.setAction_(mode_sel)
		sync_sel = NSSelectorFromString('syncToggled:')
		self._mainSync.setTarget_(self)
		self._mainSync.setAction_(sync_sel)
		self._subSync.setTarget_(self)
		self._subSync.setAction_(sync_sel)
		shape_sel = NSSelectorFromString('shapeChanged:')
		self._radioSquare.setTarget_(self)
		self._radioSquare.setAction_(shape_sel)
		self._radioTriangle.setTarget_(self)
		self._radioTriangle.setAction_(shape_sel)
		orient_sel = NSSelectorFromString('orientationChanged:')
		self._radioHorizontal.setTarget_(self)
		self._radioHorizontal.setAction_(orient_sel)
		self._radioVertical.setTarget_(self)
		self._radioVertical.setAction_(orient_sel)
		reset_sel = NSSelectorFromString('resetToDefaults:')
		self._resetButton.setTarget_(self)
		self._resetButton.setAction_(reset_sel)

	def _applyLocalisation(self):
		lx = Glyphs.localize
		self.panel.setTitle_(lx({
			'en': 'Snapping Grid Settings',
			'ja': 'スナッピンググリッドの設定',
			'zh': '吸附网格设置',
			'ko': '스냅 그리드 설정',
		}))
		self._labelGridMode.setStringValue_(lx({
			'en': 'Grid Mode:',
			'ja': 'グリッド方式:',
			'zh': '网格方式:',
			'ko': '그리드 방식:',
		}))
		self._radioDivision.setTitle_(lx({'en': 'Division', 'ja': '分割数', 'zh': '分割数', 'ko': '분할 수'}))
		self._radioUnit.setTitle_(lx({'en': 'Unit', 'ja': 'Unit数', 'zh': 'Unit数', 'ko': 'Unit 수'}))
		self._labelMainGrid.setStringValue_(lx({'en': 'Main Grid', 'ja': 'メイングリッド', 'zh': '主网格', 'ko': '메인 그리드'}))
		self._mainSync.setTitle_(lx({'en': 'Sync H/V', 'ja': '縦横同期', 'zh': '同步H/V', 'ko': 'H/V 동기화'}))
		self._labelSubGrid.setStringValue_(lx({
			'en': 'Sub Grid (main subdivisions)',
			'ja': 'サブグリッド（メインの分割数）',
			'zh': '子网格（主网格分割数）',
			'ko': '서브 그리드（메인 분할 수）',
		}))
		self._subSync.setTitle_(lx({'en': 'Sync H/V', 'ja': '縦横同期', 'zh': '同步H/V', 'ko': 'H/V 동기화'}))
		self._labelMainColor.setStringValue_(lx({'en': 'Main Color:', 'ja': 'メイン色:', 'zh': '主色:', 'ko': '메인 색상:'}))
		self._labelSubColor.setStringValue_(lx({'en': 'Sub Color:', 'ja': 'サブ色:', 'zh': '子色:', 'ko': '서브 색상:'}))
		self._snapCheck.setTitle_(lx({'en': 'Enable snap', 'ja': 'スナップを有効にする', 'zh': '启用吸附', 'ko': '스냅 활성화'}))
		self._cancelButton.setTitle_(lx({'en': 'Cancel', 'ja': 'キャンセル', 'zh': '取消', 'ko': '취소'}))
		self._okButton.setTitle_(lx({'en': 'OK', 'ja': 'OK', 'zh': 'OK', 'ko': 'OK'}))
		self._labelGridShape.setStringValue_(lx({
			'en': 'Grid Shape:',
			'ja': 'グリッド形状:',
			'zh': '网格形状:',
			'ko': '그리드 형태:',
		}))
		self._radioSquare.setTitle_(lx({'en': 'Square', 'ja': '方眼', 'zh': '方格', 'ko': '사각형'}))
		self._radioTriangle.setTitle_(lx({'en': 'Triangle', 'ja': '三角形', 'zh': '三角形', 'ko': '삼각형'}))
		self._labelOrientation.setStringValue_(lx({
			'en': 'Orientation:',
			'ja': '方向:',
			'zh': '方向:',
			'ko': '방향:',
		}))
		self._radioHorizontal.setTitle_(lx({'en': 'Horizontal', 'ja': '水平', 'zh': '水平', 'ko': '수평'}))
		self._radioVertical.setTitle_(lx({'en': 'Vertical', 'ja': '垂直', 'zh': '垂直', 'ko': '수직'}))
		self._resetButton.setTitle_(lx({'en': 'Reset', 'ja': 'リセット', 'zh': '重置', 'ko': '초기화'}))
		self._applyReadableColours()

	@objc.python_method
	def _applyReadableColours(self):
		"""Glyphs の外観下でラベル色が誤解釈されることがあるため、明示的にコントラストを確保する。"""
		label_colour = NSColor.labelColor()
		control_colour = NSColor.controlTextColor()
		editable = {self._mainH, self._mainV, self._subH, self._subV}

		def visit(view):
			if view is None:
				return
			if isinstance(view, NSTextField):
				if view in editable:
					view.setTextColor_(control_colour)
				elif not view.isEditable():
					view.setTextColor_(label_colour)
			for sub in view.subviews():
				visit(sub)

		visit(self.panel.contentView())

		for btn in (self._radioDivision, self._radioUnit, self._mainSync, self._subSync, self._snapCheck,
		            self._radioSquare, self._radioTriangle, self._radioHorizontal, self._radioVertical):
			self._setButtonTitleColour_(btn, label_colour)
		for btn in (self._cancelButton, self._okButton):
			self._setButtonTitleColour_(btn, control_colour)

	@objc.python_method
	def _setButtonTitleColour_(self, button, colour):
		if button is None:
			return
		title = button.title()
		font = button.font()
		if font is None:
			font = NSFont.systemFontOfSize_(NSFont.systemFontSize())
		attrs = {
			NSForegroundColorAttributeName: colour,
			NSFontAttributeName: font,
		}
		attr_title = NSAttributedString.alloc().initWithString_attributes_(title, attrs)
		button.setAttributedTitle_(attr_title)

	def _loadToUI(self):
		self._loadFromDict(self.plugin._getSettings(Glyphs.font))

	@objc.python_method
	def _loadFromDict(self, s):
		"""UI コントロールを設定 dict で更新する。"""
		mode = s.get('mode', 'division')
		if mode == 'unit':
			self._radioUnit.setState_(1)
			self._radioDivision.setState_(0)
		else:
			self._radioDivision.setState_(1)
			self._radioUnit.setState_(0)

		self._applyMainGridFieldsFromSettings(s)

		self._mainSync.setState_(1 if s.get('mainSync', False) else 0)
		self._subH.setStringValue_(str(int(s.get('subDivX', 2))))
		self._subV.setStringValue_(str(int(s.get('subDivY', 2))))
		self._subHStep.setIntValue_(int(s.get('subDivX', 2)))
		self._subVStep.setIntValue_(int(s.get('subDivY', 2)))
		self._subSync.setState_(1 if s.get('subSync', False) else 0)

		mc = s.get('mainColor', [0.2, 0.5, 1.0, 0.4])
		sc = s.get('subColor',  [0.2, 0.5, 1.0, 0.15])
		self._mainColorWell.setColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(mc[0], mc[1], mc[2], mc[3]))
		self._subColorWell.setColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(sc[0], sc[1], sc[2], sc[3]))

		shape = s.get('gridShape', 'square')
		if shape == 'triangle':
			self._radioTriangle.setState_(1)
			self._radioSquare.setState_(0)
		else:
			self._radioSquare.setState_(1)
			self._radioTriangle.setState_(0)
		orient = s.get('triOrientation', 'horizontal')
		if orient == 'vertical':
			self._radioVertical.setState_(1)
			self._radioHorizontal.setState_(0)
		else:
			self._radioHorizontal.setState_(1)
			self._radioVertical.setState_(0)
		self._updateOrientationAvailability()

		self._snapCheck.setState_(1 if s.get('snapEnabled', True) else 0)
		if self._mainSync.state() == 1:
			self._propagateMainHToV()
		if self._subSync.state() == 1:
			self._propagateSubHToV()
		self._updateSyncFieldAvailability()
		self._updateSubGridCaptionForMode()

	@objc.python_method
	def _applyMainGridFieldsFromSettings(self, s):
		if self._radioUnit.state() == 1:
			hv = (int(s.get('mainUnitX', 100)), int(s.get('mainUnitY', 100)))
		else:
			hv = (int(s.get('mainDivX', 4)), int(s.get('mainDivY', 4)))
		self._mainH.setStringValue_(str(hv[0]))
		self._mainV.setStringValue_(str(hv[1]))
		self._mainHStep.setIntValue_(hv[0])
		self._mainVStep.setIntValue_(hv[1])

	@objc.python_method
	def _updateSubGridCaptionForMode(self):
		lx = Glyphs.localize
		if self._radioUnit.state() == 1:
			self._labelSubGrid.setStringValue_(lx({
				'en': 'Sub Grid (subdivisions of main spacing)',
				'ja': 'サブグリッド（メイン間隔の分割数）',
				'zh': '子网格（主间距分割数）',
				'ko': '서브 그리드（메인 간격 분할 수）',
			}))
		else:
			self._labelSubGrid.setStringValue_(lx({
				'en': 'Sub Grid (main subdivisions)',
				'ja': 'サブグリッド（メインの分割数）',
				'zh': '子网格（主网格分割数）',
				'ko': '서브 그리드（메인 분할 수）',
			}))

	@objc.python_method
	def _updateSyncFieldAvailability(self):
		main_on = self._mainSync.state() == 1
		for ctl in (self._mainV, self._mainVStep):
			if ctl is not None:
				ctl.setEnabled_(not main_on)
		if self._captionMainV is not None:
			self._captionMainV.setEnabled_(not main_on)
		sub_on = self._subSync.state() == 1
		for ctl in (self._subV, self._subVStep):
			if ctl is not None:
				ctl.setEnabled_(not sub_on)
		if self._captionSubV is not None:
			self._captionSubV.setEnabled_(not sub_on)

	def _saveFromUI(self):
		mode = 'division' if self._radioDivision.state() == 1 else 'unit'
		hVal = max(1, int(float(self._mainH.stringValue() or '1')))
		vVal = max(1, int(float(self._mainV.stringValue() or '1')))
		if self._mainSync.state() == 1:
			vVal = hVal
		sx = max(1, int(float(self._subH.stringValue() or '1')))
		sy = max(1, int(float(self._subV.stringValue() or '1')))
		if self._subSync.state() == 1:
			sy = sx

		mc_ns = self._mainColorWell.color().colorUsingColorSpaceName_('NSCalibratedRGBColorSpace')
		sc_ns = self._subColorWell.color().colorUsingColorSpaceName_('NSCalibratedRGBColorSpace')
		mc = [mc_ns.redComponent(), mc_ns.greenComponent(), mc_ns.blueComponent(), mc_ns.alphaComponent()] if mc_ns else [0.2, 0.5, 1.0, 0.4]
		sc = [sc_ns.redComponent(), sc_ns.greenComponent(), sc_ns.blueComponent(), sc_ns.alphaComponent()] if sc_ns else [0.2, 0.5, 1.0, 0.15]

		prev = self.plugin._getSettings(Glyphs.font)
		s = {
			'mode':           mode,
			'mainDivX':       hVal if mode == 'division' else prev.get('mainDivX', 4),
			'mainDivY':       vVal if mode == 'division' else prev.get('mainDivY', 4),
			'mainUnitX':      hVal if mode == 'unit'     else prev.get('mainUnitX', 100),
			'mainUnitY':      vVal if mode == 'unit'     else prev.get('mainUnitY', 100),
			'mainSync':       self._mainSync.state() == 1,
			'subDivX':        sx,
			'subDivY':        sy,
			'subSync':        self._subSync.state() == 1,
			'mainColor':      mc,
			'subColor':       sc,
			'snapEnabled':    self._snapCheck.state() == 1,
			'gridShape':      'triangle' if self._radioTriangle.state() == 1 else 'square',
			'triOrientation': 'vertical' if self._radioVertical.state() == 1 else 'horizontal',
		}
		self.plugin._saveSettings(Glyphs.font, s)

	def modeChanged_(self, sender):
		# NSButton radio は兄弟間で自動排他されないことがある。sender を基準に明示的に片方だけ ON にする。
		if sender is self._radioUnit:
			self._radioUnit.setState_(1)
			self._radioDivision.setState_(0)
		elif sender is self._radioDivision:
			self._radioDivision.setState_(1)
			self._radioUnit.setState_(0)
		else:
			if self._radioUnit.state() == 1:
				self._radioDivision.setState_(0)
			elif self._radioDivision.state() == 1:
				self._radioUnit.setState_(0)
			else:
				self._radioDivision.setState_(1)
				self._radioUnit.setState_(0)
		self._applyMainGridFieldsFromSettings(self.plugin._getSettings(Glyphs.font))
		self._updateSubGridCaptionForMode()
		if self._mainSync.state() == 1:
			self._propagateMainHToV()
		if self._subSync.state() == 1:
			self._propagateSubHToV()
		self._updateSyncFieldAvailability()

	def syncToggled_(self, sender):
		if sender is self._mainSync and self._mainSync.state() == 1:
			self._propagateMainHToV()
		elif sender is self._subSync and self._subSync.state() == 1:
			self._propagateSubHToV()
		self._updateSyncFieldAvailability()

	def shapeChanged_(self, sender):
		if sender is self._radioTriangle:
			self._radioTriangle.setState_(1)
			self._radioSquare.setState_(0)
		else:
			self._radioSquare.setState_(1)
			self._radioTriangle.setState_(0)
		self._updateOrientationAvailability()

	def orientationChanged_(self, sender):
		if sender is self._radioVertical:
			self._radioVertical.setState_(1)
			self._radioHorizontal.setState_(0)
		else:
			self._radioHorizontal.setState_(1)
			self._radioVertical.setState_(0)

	def resetToDefaults_(self, sender):
		self._loadFromDict(self.plugin._defaultSettings())

	@objc.python_method
	def _updateOrientationAvailability(self):
		is_tri = self._radioTriangle.state() == 1
		for ctl in (self._labelOrientation, self._radioHorizontal, self._radioVertical):
			if ctl is not None:
				ctl.setEnabled_(is_tri)

	@objc.python_method
	def _propagateMainHToV(self):
		self._mainV.setStringValue_(self._mainH.stringValue())
		self._syncStepperFromField(self._mainV, self._mainVStep)

	@objc.python_method
	def _propagateSubHToV(self):
		self._subV.setStringValue_(self._subH.stringValue())
		self._syncStepperFromField(self._subV, self._subVStep)

	def stepperChanged_(self, sender):
		if self._isUpdatingControls:
			return
		field = None
		for step, f in self._stepperPairs:
			if sender is step:
				field = f
				break
		if field:
			self._isUpdatingControls = True
			try:
				val = int(sender.intValue())
				field.setStringValue_(str(val))
				# Sync paired field if needed
				isMain = (sender is self._mainHStep or sender is self._mainVStep)
				if isMain and self._mainSync.state() == 1:
					self._mainH.setStringValue_(str(val))
					self._mainV.setStringValue_(str(val))
					self._mainHStep.setIntValue_(val)
					self._mainVStep.setIntValue_(val)
				elif not isMain and self._subSync.state() == 1:
					self._subH.setStringValue_(str(val))
					self._subV.setStringValue_(str(val))
					self._subHStep.setIntValue_(val)
					self._subVStep.setIntValue_(val)
			finally:
				self._isUpdatingControls = False

	def controlTextDidEndEditing_(self, notification):
		obj = notification.object()
		if obj is self._mainH:
			self._syncStepperFromField(self._mainH, self._mainHStep)
			if self._mainSync.state() == 1:
				self._propagateMainHToV()
		elif obj is self._mainV:
			self._syncStepperFromField(self._mainV, self._mainVStep)
			if self._mainSync.state() == 1:
				self._propagateMainHToV()
		elif obj is self._subH:
			self._syncStepperFromField(self._subH, self._subHStep)
			if self._subSync.state() == 1:
				self._propagateSubHToV()
		elif obj is self._subV:
			self._syncStepperFromField(self._subV, self._subVStep)
			if self._subSync.state() == 1:
				self._propagateSubHToV()

	@objc.python_method
	def _syncStepperFromField(self, field, stepper):
		try:
			val = max(1, min(999, int(float(field.stringValue() or '1'))))
		except (TypeError, ValueError):
			val = 1
		self._isUpdatingControls = True
		try:
			field.setStringValue_(str(val))
			stepper.setIntValue_(val)
		finally:
			self._isUpdatingControls = False

	def ok_(self, sender):
		self._saveFromUI()
		self.panel.orderOut_(None)
		self.plugin._loadPrefs()
		Glyphs.redraw()

	def cancel_(self, sender):
		self.panel.orderOut_(None)


# ─────────────────────────────────────────────
# Plugin
# ─────────────────────────────────────────────

class SnappingGrid(GeneralPlugin):

	@objc.python_method
	def settings(self):
		self.name = Glyphs.localize({
			'en': 'Snapping Grid',
			'ja': 'スナッピンググリッド',
			'zh': '吸附网格',
			'ko': '스냅 그리드',
		})

	@objc.python_method
	def start(self):
		self._loadPrefs()
		self._settingsController = SettingsPanelController.alloc().initWithPlugin_(self)

		showLabel = Glyphs.localize({
			'en': 'Show Snapping Grid',
			'ja': 'スナッピンググリッドを表示',
			'zh': '显示吸附网格',
			'ko': '스냅 그리드 표시',
		})
		if Glyphs.versionNumber >= 3.3:
			self._showItem = NSMenuItem(showLabel, callback=self._toggleGrid_, target=self)
		else:
			self._showItem = NSMenuItem(showLabel, self._toggleGrid_)
		self._showItem.setState_(1 if self.gridVisible else 0)
		Glyphs.menu[VIEW_MENU].append(self._showItem)

		settingsLabel = Glyphs.localize({
			'en': 'Snapping Grid Settings\u2026',
			'ja': 'スナッピンググリッドの設定\u2026',
			'zh': '吸附网格设置\u2026',
			'ko': '스냅 그리드 설정\u2026',
		})
		if Glyphs.versionNumber >= 3.3:
			settingsItem = NSMenuItem(settingsLabel, callback=self._showSettings_, target=self)
		else:
			settingsItem = NSMenuItem(settingsLabel, self._showSettings_)
		inserted = False
		try:
			main_menu = NSApp.mainMenu()
			for top_item in main_menu.itemArray():
				submenu = top_item.submenu()
				if submenu is None:
					continue
				for i, item in enumerate(submenu.itemArray()):
					if 'Master Grid' in (item.title() or ''):
						submenu.insertItem_atIndex_(settingsItem, i + 1)
						inserted = True
						break
				if inserted:
					break
		except Exception:
			pass
		if not inserted:
			Glyphs.menu[EDIT_MENU].append(settingsItem)

		Glyphs.addCallback(self._drawGrid_, DRAWBACKGROUND)
		Glyphs.addCallback(self._snapDuringDrag_, MOUSEDRAGGED)
		Glyphs.addCallback(self._snapDuringDrag_, MOUSEUP)

	def _toggleGrid_(self, sender):
		self.gridVisible = not self.gridVisible
		self._showItem.setState_(1 if self.gridVisible else 0)
		Glyphs.defaults[PREF + '.gridVisible'] = self.gridVisible
		Glyphs.redraw()

	def _showSettings_(self, sender):
		self._settingsController.show()

	def _snapDuringDrag_(self, notification):
		if not self.gridVisible:
			return
		try:
			font = Glyphs.font
			if not font:
				return
			layers = font.selectedLayers
			if not layers:
				return
			layer = layers[0]
			s = self._getSettings(font)
			if not s.get('snapEnabled', True):
				return
			mainX, mainY = self._mainIntervals(layer, s)
			if mainX <= 0 or mainY <= 0:
				return
			# Snap to the finest (sub) grid so both main and sub lines are targets
			stepX, stepY = self._subIntervals(s, mainX, mainY)
			if stepX <= 0 or stepY <= 0:
				stepX, stepY = mainX, mainY

			ySnapOrigin = self._ySnapOriginForLayer(layer, s)
			pivot = self._shearPivotY(layer)

			# Only operate on GSNode items (skip anchors, components)
			selectedNodes = [n for n in layer.selection
			                 if hasattr(n, 'position') and hasattr(n, 'type')]
			if not selectedNodes:
				return
			selectedSet = set(selectedNodes)

			moves = {}
			angle_deg = self._effectiveItalicAngleDegrees(layer)
			tan_shear = math.tan(math.radians(angle_deg))
			shape = s['gridShape']

			for node in selectedNodes:
				pos = node.position
				# Un-shear to glyph space (italic shear is applied to grid lines but not stored positions)
				if abs(tan_shear) < 1e-15:
					pu, pv = pos.x, pos.y
				else:
					pu = pos.x - tan_shear * (pos.y - pivot)
					pv = pos.y

				if shape == 'triangle':
					orient = s['triOrientation']
					if orient == 'horizontal':
						# Lattice: P(m,n) = (m*stepX + n*stepX/2, n*stepY + ySnapOrigin)
						n_snap = round((pv - ySnapOrigin) / stepY)
						m_snap = round((pu - n_snap * stepX * 0.5) / stepX)
						su = m_snap * stepX + n_snap * stepX * 0.5
						sv = n_snap * stepY + ySnapOrigin
					else:
						# Lattice: P(m,n) = (n*stepX, m*stepY + n*stepY/2)
						n_snap = round(pu / stepX)
						m_snap = round((pv - n_snap * stepY * 0.5) / stepY)
						su = n_snap * stepX
						sv = m_snap * stepY + n_snap * stepY * 0.5
					snappedX = su + tan_shear * (sv - pivot)
					snappedY = sv
				else:
					# Square grid: snap u and y independently
					snappedY = round((pv - ySnapOrigin) / stepY) * stepY + ySnapOrigin
					u_snapped = round(pu / stepX) * stepX
					snappedX = u_snapped + tan_shear * (snappedY - pivot)

				dx = snappedX - pos.x
				dy = snappedY - pos.y
				if abs(dx) > 1e-6 or abs(dy) > 1e-6:
					moves[id(node)] = (node, dx, dy)

			# Propagate delta to adjacent handles for on-curve nodes
			# (only if the handle itself is not part of the user selection)
			for nid, (node, dx, dy) in list(moves.items()):
				if node.type == OFFCURVE:
					continue
				for neighbor in (node.prevNode, node.nextNode):
					if neighbor is None:
						continue
					if neighbor.type != OFFCURVE:
						continue
					if neighbor in selectedSet:
						continue
					if id(neighbor) in moves:
						continue
					moves[id(neighbor)] = (neighbor, dx, dy)

			# Apply all moves
			for node, dx, dy in moves.values():
				p = node.position
				node.position = NSPoint(p.x + dx, p.y + dy)
		except Exception:
			print(traceback.format_exc())

	@objc.python_method
	def _drawGrid_(self, layer, info):
		if not self.gridVisible:
			return
		try:
			width = layer.width
			master = layer.associatedFontMaster()
			yTop = master.ascender if master else 800.0
			yBottom = master.descender if master else -200.0
			scale = info.get('Scale', 1.0) if isinstance(info, dict) else 1.0
			lineWidth = 1.0 / scale

			s = self._getSettings(Glyphs.font)
			mainX, mainY = self._mainIntervals(layer, s)
			subX, subY = self._subIntervals(s, mainX, mainY)
			grid_mode = s['mode']

			pivot_y = self._shearPivotY(layer)
			shape = s['gridShape']
			if shape == 'triangle':
				orient = s['triOrientation']
				y_origin = 0.0 if grid_mode == 'unit' else yBottom
				if subX > 0 and subY > 0:
					self._strokeTriGrid(width, yTop, yBottom, subX, subY, lineWidth, self._colorFromList(s['subColor']), orient, y_origin, layer, pivot_y)
				if mainX > 0 and mainY > 0:
					self._strokeTriGrid(width, yTop, yBottom, mainX, mainY, lineWidth, self._colorFromList(s['mainColor']), orient, y_origin, layer, pivot_y)
			else:
				if subX > 0 and subY > 0:
					self._strokeGrid(width, yTop, yBottom, subX, subY, lineWidth, self._colorFromList(s['subColor']), grid_mode, layer, pivot_y)
				if mainX > 0 and mainY > 0:
					self._strokeGrid(width, yTop, yBottom, mainX, mainY, lineWidth, self._colorFromList(s['mainColor']), grid_mode, layer, pivot_y)
		except Exception:
			print(traceback.format_exc())

	@objc.python_method
	def _strokeGrid(self, width, yTop, yBottom, stepX, stepY, lineWidth, color, grid_mode, layer, pivot_y):
		color.set()
		path = NSBezierPath.alloc().init()
		path.setLineWidth_(lineWidth)

		# Draw in glyph coordinate space (straight vertical / horizontal lines).
		# Vertical lines
		u = stepX
		while u < width:
			path.moveToPoint_(NSPoint(u, yBottom))
			path.lineToPoint_(NSPoint(u, yTop))
			u += stepX

		# Horizontal lines
		if stepY > 0:
			y_origin = 0.0 if grid_mode == 'unit' else yBottom
			n = int(math.ceil((yBottom - y_origin) / stepY))
			y = y_origin + n * stepY
			while y <= yTop:
				path.moveToPoint_(NSPoint(0.0,   y))
				path.lineToPoint_(NSPoint(width, y))
				y += stepY

		# Apply italic shear via Glyphs API (same pivot used by Glyphs itself).
		angle_deg = self._effectiveItalicAngleDegrees(layer)
		if abs(angle_deg) > 0.001:
			path.transformWithAngle_center_(angle_deg, pivot_y)

		path.stroke()

	@objc.python_method
	def _strokeTriGrid(self, width, yTop, yBottom, stepX, stepY, lineWidth, color, orientation, y_origin, layer, pivot_y):
		if orientation == 'vertical':
			self._strokeTriGridV(width, yTop, yBottom, stepX, stepY, lineWidth, color, y_origin, layer, pivot_y)
		else:
			self._strokeTriGridH(width, yTop, yBottom, stepX, stepY, lineWidth, color, y_origin, layer, pivot_y)

	@objc.python_method
	def _strokeTriGridH(self, width, yTop, yBottom, stepX, stepY, lineWidth, color, y_origin, layer, pivot_y):
		"""Horizontal tri-grid: horizontal lines + ±diagonal lines (slope = 2*stepY/stepX)."""
		color.set()
		path = NSBezierPath.alloc().init()
		path.setLineWidth_(lineWidth)
		slope = 2.0 * stepY / stepX

		# Horizontal lines, anchored at y_origin
		n_start = int(math.floor((yBottom - y_origin) / stepY))
		n_end = int(math.ceil((yTop - y_origin) / stepY))
		for n in range(n_start, n_end + 1):
			y = y_origin + n * stepY
			if yBottom <= y <= yTop:
				path.moveToPoint_(NSPoint(0.0, y))
				path.lineToPoint_(NSPoint(width, y))

		# Diagonal lines pass through (m*stepX, y_origin).
		# "/" : y - y_origin = slope*(x - m*stepX)  →  x = (y-y_origin)/slope + m*stepX
		# "\" : y - y_origin = -slope*(x - m*stepX) →  x = m*stepX - (y-y_origin)/slope
		extra = int(math.ceil((abs(yTop - y_origin) + abs(yBottom - y_origin)) / slope / stepX)) + 2
		m_min = -extra
		m_max = int(math.ceil(width / stepX)) + extra

		for m in range(m_min, m_max + 1):
			# "/"
			x0 = (yBottom - y_origin) / slope + m * stepX
			x1 = (yTop - y_origin) / slope + m * stepX
			if not (x1 < 0 or x0 > width):
				path.moveToPoint_(NSPoint(x0, yBottom))
				path.lineToPoint_(NSPoint(x1, yTop))
			# "\"
			x0b = m * stepX - (yBottom - y_origin) / slope
			x1b = m * stepX - (yTop - y_origin) / slope
			if not (x1b > width or x0b < 0):
				path.moveToPoint_(NSPoint(x0b, yBottom))
				path.lineToPoint_(NSPoint(x1b, yTop))

		angle_deg = self._effectiveItalicAngleDegrees(layer)
		if abs(angle_deg) > 0.001:
			path.transformWithAngle_center_(angle_deg, pivot_y)
		path.stroke()

	@objc.python_method
	def _strokeTriGridV(self, width, yTop, yBottom, stepX, stepY, lineWidth, color, y_origin, layer, pivot_y):
		"""Vertical tri-grid: vertical lines + ±diagonal lines (slope = stepY/(2*stepX))."""
		color.set()
		path = NSBezierPath.alloc().init()
		path.setLineWidth_(lineWidth)
		slope_v = stepY / (2.0 * stepX)

		# Vertical lines
		u = stepX
		while u < width:
			path.moveToPoint_(NSPoint(u, yBottom))
			path.lineToPoint_(NSPoint(u, yTop))
			u += stepX

		# Diagonal lines pass through (0, m*stepY + y_origin).
		# "/" : y = slope_v*x + m*stepY + y_origin
		# "\" : y = -slope_v*x + m*stepY + y_origin
		extra = int(math.ceil((abs(yTop) + abs(yBottom)) / stepY + width * slope_v / stepY)) + 2
		m_min = int(math.floor((yBottom - y_origin) / stepY)) - extra
		m_max = int(math.ceil((yTop - y_origin) / stepY)) + extra

		for m in range(m_min, m_max + 1):
			base_y = m * stepY + y_origin
			# "/"
			y_x0 = base_y
			y_xW = slope_v * width + base_y
			y_lo, y_hi = min(y_x0, y_xW), max(y_x0, y_xW)
			if not (y_hi < yBottom or y_lo > yTop):
				path.moveToPoint_(NSPoint(0.0, y_x0))
				path.lineToPoint_(NSPoint(width, y_xW))
			# "\"
			y_x0b = base_y
			y_xWb = -slope_v * width + base_y
			y_lo2, y_hi2 = min(y_x0b, y_xWb), max(y_x0b, y_xWb)
			if not (y_hi2 < yBottom or y_lo2 > yTop):
				path.moveToPoint_(NSPoint(0.0, y_x0b))
				path.lineToPoint_(NSPoint(width, y_xWb))

		angle_deg = self._effectiveItalicAngleDegrees(layer)
		if abs(angle_deg) > 0.001:
			path.transformWithAngle_center_(angle_deg, pivot_y)
		path.stroke()

	@objc.python_method
	def _ySnapOriginForLayer(self, layer, s):
		"""Y snap / horizontal grid phase: baseline (0) in Unit mode, descender in Division mode."""
		if s.get('mode', 'division') == 'unit':
			return 0.0
		master = layer.associatedFontMaster()
		return master.descender if master else -200.0

	@objc.python_method
	def _glyphScriptTag(self, glyph):
		if glyph is None:
			return ''
		try:
			tag = glyph.script
		except Exception:
			tag = None
		if tag is None:
			return ''
		return str(tag).strip().lower()

	@objc.python_method
	def _scripts_match_for_italic_cp(self, param_script, glyph_script):
		ps = (param_script or '').strip().lower()
		gs = (glyph_script or '').strip().lower()
		if not ps or not gs:
			return False
		if ps == gs:
			return True
		# Friendly names vs common OpenType / Glyphs script tags
		groups = (
			frozenset(('latin', 'latn')),
			frozenset(('kana', 'jpan', 'japanese')),
			frozenset(('hani', 'hans', 'hant')),
		)
		for g in groups:
			if ps in g and gs in g:
				return True
		return False

	@objc.python_method
	def _iter_custom_parameter_values_named(self, source, name):
		if source is None:
			return
		cps = getattr(source, 'customParameters', None)
		if not cps:
			return
		for p in cps:
			pname = getattr(p, 'name', None)
			if pname is None and hasattr(p, 'key'):
				try:
					pname = p.key()
				except Exception:
					pname = None
			if pname != name:
				continue
			val = getattr(p, 'value', None)
			yield val

	@objc.python_method
	def _shearPivotY(self, layer):
		"""Y pivot for italic shear. Uses master.slantHeightForLayer_, falls back to xHeight/2."""
		master = layer.associatedFontMaster() if layer else None
		if master is None:
			return 0.0
		try:
			v = master.slantHeightForLayer_(layer)
			if v is not None:
				return float(v)
		except Exception:
			pass
		xh = getattr(master, 'xHeight', None)
		return float(xh) * 0.5 if xh else 0.0

	@objc.python_method
	def _effectiveItalicAngleDegrees(self, layer):
		"""Italic angle for grid shear. Prefers master.italicAngleForLayer_ (handles script CPs)."""
		master = layer.associatedFontMaster() if layer else None
		if master is None:
			return 0.0
		try:
			a = master.italicAngleForLayer_(layer)
			if a is not None:
				return float(a)
		except Exception:
			pass
		# Fallback: manual script-specific custom parameter parsing
		glyph = layer.parent if layer else None
		font = glyph.parent if glyph and getattr(glyph, 'parent', None) else None
		gscript = self._glyphScriptTag(glyph)
		for source in (master, font):
			for raw in self._iter_custom_parameter_values_named(source, 'italicAngle'):
				text = str(raw).strip()
				if ':' in text:
					seg, rest = text.split(':', 1)
					try:
						angle = float(rest.strip())
					except (TypeError, ValueError):
						continue
					if self._scripts_match_for_italic_cp(seg, gscript):
						return float(angle)
		for source in (master, font):
			for raw in self._iter_custom_parameter_values_named(source, 'italicAngle'):
				text = str(raw).strip()
				if ':' not in text:
					try:
						return float(text)
					except (TypeError, ValueError):
						continue
		return float(getattr(master, 'italicAngle', 0.0) or 0.0)

	@objc.python_method
	def _mainIntervals(self, layer, s):
		mode = s.get('mode', 'division')
		if mode == 'unit':
			x = float(s.get('mainUnitX', 100))
			y = float(s.get('mainUnitY', 100))
		else:
			divX = max(1, int(s.get('mainDivX', 4)))
			divY = max(1, int(s.get('mainDivY', 4)))
			master = layer.associatedFontMaster()
			height = (master.ascender - master.descender) if master else 1000.0
			x = layer.width / divX
			y = height / divY
		return x, y

	@objc.python_method
	def _subIntervals(self, s, mainX, mainY):
		subDivX = max(1, int(s.get('subDivX', 2)))
		subDivY = max(1, int(s.get('subDivY', 2)))
		return mainX / subDivX, mainY / subDivY

	@objc.python_method
	def _colorFromList(self, rgba):
		return NSColor.colorWithCalibratedRed_green_blue_alpha_(rgba[0], rgba[1], rgba[2], rgba[3])

	@objc.python_method
	def _defaultSettings(self):
		return {
			'mode':           'division',
			'mainDivX':       4,
			'mainDivY':       4,
			'mainUnitX':      100,
			'mainUnitY':      100,
			'mainSync':       False,
			'subDivX':        2,
			'subDivY':        2,
			'subSync':        False,
			'mainColor':      [0.2, 0.5, 1.0, 0.4],
			'subColor':       [0.2, 0.5, 1.0, 0.15],
			'snapEnabled':    True,
			'gridShape':      'square',
			'triOrientation': 'horizontal',
		}

	@objc.python_method
	def _getSettings(self, font):
		"""font.userData → Glyphs.defaults（後方互換）→ ハードコードの順でフォールバック。"""
		if font:
			ud = font.userData.get('com.palf.SnappingGrid', None)
			if ud:
				s = self._defaultSettings()
				s.update(ud)
				return s
		# Glyphs.defaults からのレガシーフォールバック
		p = PREF; d = Glyphs.defaults
		return {
			'mode':           d.get(p + '.mode', 'division'),
			'mainDivX':       int(d.get(p + '.mainDivX', 4)),
			'mainDivY':       int(d.get(p + '.mainDivY', 4)),
			'mainUnitX':      int(d.get(p + '.mainUnitX', 100)),
			'mainUnitY':      int(d.get(p + '.mainUnitY', 100)),
			'mainSync':       bool(d.get(p + '.mainSync', False)),
			'subDivX':        int(d.get(p + '.subDivX', 2)),
			'subDivY':        int(d.get(p + '.subDivY', 2)),
			'subSync':        bool(d.get(p + '.subSync', False)),
			'mainColor':      [float(d.get(p + '.mainR', 0.2)), float(d.get(p + '.mainG', 0.5)),
			                   float(d.get(p + '.mainB', 1.0)), float(d.get(p + '.mainA', 0.4))],
			'subColor':       [float(d.get(p + '.subR',  0.2)), float(d.get(p + '.subG',  0.5)),
			                   float(d.get(p + '.subB',  1.0)), float(d.get(p + '.subA',  0.15))],
			'snapEnabled':    bool(d.get(p + '.snapEnabled', True)),
			'gridShape':      d.get(p + '.gridShape', 'square'),
			'triOrientation': d.get(p + '.triOrientation', 'horizontal'),
		}

	@objc.python_method
	def _saveSettings(self, font, s):
		"""font.userData に保存し、Glyphs.defaults にも書いて新規フォント用テンプレートを更新する。"""
		if font:
			font.userData['com.palf.SnappingGrid'] = s
		p = PREF; d = Glyphs.defaults
		d[p + '.mode']           = s['mode']
		d[p + '.mainDivX']       = s['mainDivX'];    d[p + '.mainDivY']  = s['mainDivY']
		d[p + '.mainUnitX']      = s['mainUnitX'];   d[p + '.mainUnitY'] = s['mainUnitY']
		d[p + '.mainSync']       = s['mainSync']
		d[p + '.subDivX']        = s['subDivX'];     d[p + '.subDivY']   = s['subDivY']
		d[p + '.subSync']        = s['subSync']
		mc = s['mainColor']
		d[p + '.mainR'] = mc[0]; d[p + '.mainG'] = mc[1]; d[p + '.mainB'] = mc[2]; d[p + '.mainA'] = mc[3]
		sc = s['subColor']
		d[p + '.subR']  = sc[0]; d[p + '.subG']  = sc[1]; d[p + '.subB']  = sc[2]; d[p + '.subA']  = sc[3]
		d[p + '.snapEnabled']    = s['snapEnabled']
		d[p + '.gridShape']      = s['gridShape']
		d[p + '.triOrientation'] = s['triOrientation']

	@objc.python_method
	def _loadPrefs(self):
		self.gridVisible = bool(Glyphs.defaults.get(PREF + '.gridVisible', True))

	@objc.python_method
	def __file__(self):
		return __file__

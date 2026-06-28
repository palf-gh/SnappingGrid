# encoding: utf-8
from __future__ import division, print_function, unicode_literals
import objc
import traceback
import os
import math
from GlyphsApp import Glyphs, EDIT_MENU, VIEW_MENU, DRAWBACKGROUND, MOUSEDRAGGED, MOUSEUP, OFFCURVE
from GlyphsApp.plugins import GeneralPlugin
from AppKit import (
	NSApplication,
	NSMenuItem, NSColor, NSBezierPath, NSPoint,
	NSTextField, NSStepper, NSButton, NSColorWell,
	NSBundle, NSNib,
	NSAttributedString, NSFont, NSForegroundColorAttributeName, NSFontAttributeName,
	NSEvent,
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
	_labelGridGap    = objc.IBOutlet()
	_gapEnable       = objc.IBOutlet()
	_gapSyncMainSub  = objc.IBOutlet()
	_labelMainGap    = objc.IBOutlet()
	_captionMainGapH = objc.IBOutlet()
	_captionMainGapV = objc.IBOutlet()
	_mainGapH        = objc.IBOutlet()
	_mainGapV        = objc.IBOutlet()
	_mainGapHStep    = objc.IBOutlet()
	_mainGapVStep    = objc.IBOutlet()
	_gapSyncHV       = objc.IBOutlet()
	_labelSubGap     = objc.IBOutlet()
	_captionSubGapH  = objc.IBOutlet()
	_captionSubGapV  = objc.IBOutlet()
	_subGapH         = objc.IBOutlet()
	_subGapV         = objc.IBOutlet()
	_subGapHStep     = objc.IBOutlet()
	_subGapVStep     = objc.IBOutlet()

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
		self.plugin._clearPreview()
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
		for step in (self._mainGapHStep, self._mainGapVStep, self._subGapHStep, self._subGapVStep):
			step.setMinValue_(0)
			step.setMaxValue_(999)
			step.setIncrement_(1)
			step.setValueWraps_(False)
			step.setTarget_(self)
			step.setAction_(step_action)
		for field in (self._mainH, self._mainV, self._subH, self._subV,
		              self._mainGapH, self._mainGapV, self._subGapH, self._subGapV):
			field.setEditable_(True)
			field.setSelectable_(True)
			field.setBezeled_(True)
			field.setDrawsBackground_(True)
			field.setDelegate_(self)
		self._stepperPairs = (
			(self._mainHStep, self._mainH, 1, 'mainGrid'),
			(self._mainVStep, self._mainV, 1, 'mainGrid'),
			(self._subHStep, self._subH, 1, 'subGrid'),
			(self._subVStep, self._subV, 1, 'subGrid'),
			(self._mainGapHStep, self._mainGapH, 0, 'mainGap'),
			(self._mainGapVStep, self._mainGapV, 0, 'mainGap'),
			(self._subGapHStep, self._subGapH, 0, 'subGap'),
			(self._subGapVStep, self._subGapV, 0, 'subGap'),
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
		gap_sel = NSSelectorFromString('gapChanged:')
		for button in (self._gapEnable, self._gapSyncMainSub, self._gapSyncHV):
			button.setTarget_(self)
			button.setAction_(gap_sel)
		preview_sel = NSSelectorFromString('previewChanged:')
		self._snapCheck.setTarget_(self)
		self._snapCheck.setAction_(preview_sel)
		colour_sel = NSSelectorFromString('colourChanged:')
		for well in (self._mainColorWell, self._subColorWell):
			well.setContinuous_(True)
			well.setTarget_(self)
			well.setAction_(colour_sel)

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
		self._labelGridGap.setStringValue_(lx({
			'en': 'Grid Gap:',
			'ja': 'グリッド間隔:',
			'zh': '网格间隔:',
			'ko': '그리드 간격:',
		}))
		self._gapEnable.setTitle_(lx({'en': 'Enable', 'ja': '有効にする', 'zh': '启用', 'ko': '활성화'}))
		self._gapSyncMainSub.setTitle_(lx({'en': 'Link Main/Sub', 'ja': 'メイン/サブ連動', 'zh': '关联主/子', 'ko': '메인/서브 연동'}))
		self._labelMainGap.setStringValue_(lx({'en': 'Main', 'ja': 'メイン', 'zh': '主', 'ko': '메인'}))
		self._labelSubGap.setStringValue_(lx({'en': 'Sub', 'ja': 'サブ', 'zh': '子', 'ko': '서브'}))
		self._gapSyncHV.setTitle_(lx({'en': 'Sync H/V', 'ja': '縦横同期', 'zh': '同步H/V', 'ko': 'H/V 동기화'}))
		self._resetButton.setTitle_(lx({'en': 'Reset', 'ja': 'リセット', 'zh': '重置', 'ko': '초기화'}))
		self._applyReadableColours()

	@objc.python_method
	def _applyReadableColours(self):
		"""Glyphs の外観下でラベル色が誤解釈されることがあるため、明示的にコントラストを確保する。"""
		label_colour = NSColor.labelColor()
		control_colour = NSColor.controlTextColor()
		editable = {
			self._mainH, self._mainV, self._subH, self._subV,
			self._mainGapH, self._mainGapV, self._subGapH, self._subGapV,
		}

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
		            self._radioSquare, self._radioTriangle, self._radioHorizontal, self._radioVertical,
		            self._gapEnable, self._gapSyncMainSub, self._gapSyncHV):
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
		self._gapEnable.setState_(1 if s.get('gapEnabled', False) else 0)
		self._gapSyncMainSub.setState_(1 if s.get('gapSyncMainSub', False) else 0)
		self._gapSyncHV.setState_(1 if s.get('gapSyncHV', False) else 0)
		self._setGapFieldValues(s)

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
		self._normaliseGapLinks()
		self._updateSyncFieldAvailability()
		self._updateSubGridCaptionForMode()
		self._updateGapAvailability()

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
	def _formatUnitValue(self, value):
		try:
			f = float(value)
		except (TypeError, ValueError):
			f = 0.0
		if abs(f - int(f)) < 1e-6:
			return str(int(f))
		return ('%.3f' % f).rstrip('0').rstrip('.')

	@objc.python_method
	def _setGapFieldValues(self, s):
		values = self.plugin._normalisedGapValues(s, include_disabled=True)
		pairs = (
			(self._mainGapH, self._mainGapHStep, values[0]),
			(self._mainGapV, self._mainGapVStep, values[1]),
			(self._subGapH, self._subGapHStep, values[2]),
			(self._subGapV, self._subGapVStep, values[3]),
		)
		for field, stepper, value in pairs:
			text = self._formatUnitValue(value)
			field.setStringValue_(text)
			stepper.setFloatValue_(float(value))

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

	@objc.python_method
	def _updateGapAvailability(self):
		is_tri = self._radioTriangle.state() == 1
		gap_on = self._gapEnable.state() == 1
		main_sub_on = self._gapSyncMainSub.state() == 1
		hv_on = self._gapSyncHV.state() == 1
		for ctl in (self._labelGridGap, self._gapEnable):
			if ctl is not None:
				ctl.setEnabled_(True)
		for ctl in (self._gapSyncMainSub, self._labelMainGap, self._captionMainGapH,
		            self._mainGapH, self._mainGapHStep):
			if ctl is not None:
				ctl.setEnabled_(gap_on)
		# Sync H/V and V fields: not applicable for triangle (V is unused)
		for ctl in (self._gapSyncHV,):
			if ctl is not None:
				ctl.setEnabled_(gap_on and not is_tri)
		for ctl in (self._captionMainGapV, self._mainGapV, self._mainGapVStep):
			if ctl is not None:
				ctl.setEnabled_(gap_on and not hv_on and not is_tri)
		for ctl in (self._labelSubGap, self._captionSubGapH, self._subGapH, self._subGapHStep):
			if ctl is not None:
				ctl.setEnabled_(gap_on and not main_sub_on)
		for ctl in (self._captionSubGapV, self._subGapV, self._subGapVStep):
			if ctl is not None:
				ctl.setEnabled_(gap_on and not main_sub_on and not hv_on and not is_tri)

	@objc.python_method
	def _fieldInt(self, field, fallback=1, minimum=1):
		try:
			return max(minimum, int(float(field.stringValue() or str(fallback))))
		except (TypeError, ValueError):
			return max(minimum, int(fallback))

	@objc.python_method
	def _fieldFloat(self, field, fallback=0.0, minimum=0.0):
		try:
			return max(minimum, float(field.stringValue() or str(fallback)))
		except (TypeError, ValueError):
			return max(minimum, float(fallback))

	@objc.python_method
	def _collectSettings(self):
		mode = 'division' if self._radioDivision.state() == 1 else 'unit'
		hVal = self._fieldInt(self._mainH, 1, 1)
		vVal = self._fieldInt(self._mainV, 1, 1)
		if self._mainSync.state() == 1:
			vVal = hVal
		sx = self._fieldInt(self._subH, 1, 1)
		sy = self._fieldInt(self._subV, 1, 1)
		if self._subSync.state() == 1:
			sy = sx
		mainGapX = self._fieldFloat(self._mainGapH, 0.0, 0.0)
		mainGapY = self._fieldFloat(self._mainGapV, 0.0, 0.0)
		subGapX = self._fieldFloat(self._subGapH, 0.0, 0.0)
		subGapY = self._fieldFloat(self._subGapV, 0.0, 0.0)
		if self._gapSyncHV.state() == 1:
			mainGapY = mainGapX
			subGapY = subGapX
		if self._gapSyncMainSub.state() == 1:
			subGapX = mainGapX
			subGapY = mainGapY

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
			'gapEnabled':     self._gapEnable.state() == 1,
			'mainGapX':       mainGapX,
			'mainGapY':       mainGapY,
			'subGapX':        subGapX,
			'subGapY':        subGapY,
			'gapSyncHV':      self._gapSyncHV.state() == 1,
			'gapSyncMainSub': self._gapSyncMainSub.state() == 1,
		}
		return s

	def _saveFromUI(self):
		self.plugin._saveSettings(Glyphs.font, self._collectSettings())

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
		self._pushPreview()

	def syncToggled_(self, sender):
		if sender is self._mainSync and self._mainSync.state() == 1:
			self._propagateMainHToV()
		elif sender is self._subSync and self._subSync.state() == 1:
			self._propagateSubHToV()
		self._updateSyncFieldAvailability()
		self._pushPreview()

	def shapeChanged_(self, sender):
		if sender is self._radioTriangle:
			self._radioTriangle.setState_(1)
			self._radioSquare.setState_(0)
		else:
			self._radioSquare.setState_(1)
			self._radioTriangle.setState_(0)
		self._updateOrientationAvailability()
		self._updateGapAvailability()
		self._pushPreview()

	def orientationChanged_(self, sender):
		if sender is self._radioVertical:
			self._radioVertical.setState_(1)
			self._radioHorizontal.setState_(0)
		else:
			self._radioHorizontal.setState_(1)
			self._radioVertical.setState_(0)
		self._pushPreview()

	def resetToDefaults_(self, sender):
		self._loadFromDict(self.plugin._defaultSettings())
		self._pushPreview()

	def previewChanged_(self, sender):
		self._pushPreview()

	def colourChanged_(self, sender):
		self._pushPreview()

	def gapChanged_(self, sender):
		self._normaliseGapLinks()
		self._updateGapAvailability()
		self._pushPreview()

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

	@objc.python_method
	def _normaliseGapLinks(self):
		if self._gapSyncHV.state() == 1:
			self._mainGapV.setStringValue_(self._mainGapH.stringValue())
			self._syncStepperFromField(self._mainGapV, self._mainGapVStep, 0)
			self._subGapV.setStringValue_(self._subGapH.stringValue())
			self._syncStepperFromField(self._subGapV, self._subGapVStep, 0)
		if self._gapSyncMainSub.state() == 1:
			self._subGapH.setStringValue_(self._mainGapH.stringValue())
			self._subGapV.setStringValue_(self._mainGapV.stringValue())
			self._syncStepperFromField(self._subGapH, self._subGapHStep, 0)
			self._syncStepperFromField(self._subGapV, self._subGapVStep, 0)

	def stepperChanged_(self, sender):
		if self._isUpdatingControls:
			return
		field = None
		minimum = 1
		kind = None
		for step, f, mn, k in self._stepperPairs:
			if sender is step:
				field = f
				minimum = mn
				kind = k
				break
		if field:
			self._isUpdatingControls = True
			try:
				val = max(minimum, int(sender.intValue()))
				field.setStringValue_(str(val))
				# Sync paired field if needed
				if kind == 'mainGrid' and self._mainSync.state() == 1:
					self._mainH.setStringValue_(str(val))
					self._mainV.setStringValue_(str(val))
					self._mainHStep.setIntValue_(val)
					self._mainVStep.setIntValue_(val)
				elif kind == 'subGrid' and self._subSync.state() == 1:
					self._subH.setStringValue_(str(val))
					self._subV.setStringValue_(str(val))
					self._subHStep.setIntValue_(val)
					self._subVStep.setIntValue_(val)
			finally:
				self._isUpdatingControls = False
			if kind in ('mainGap', 'subGap'):
				self._normaliseGapLinks()
				self._updateGapAvailability()
			self._pushPreview()

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
		elif obj is self._mainGapH:
			self._syncStepperFromField(self._mainGapH, self._mainGapHStep, 0)
			self._normaliseGapLinks()
		elif obj is self._mainGapV:
			self._syncStepperFromField(self._mainGapV, self._mainGapVStep, 0)
			self._normaliseGapLinks()
		elif obj is self._subGapH:
			self._syncStepperFromField(self._subGapH, self._subGapHStep, 0)
			self._normaliseGapLinks()
		elif obj is self._subGapV:
			self._syncStepperFromField(self._subGapV, self._subGapVStep, 0)
			self._normaliseGapLinks()
		self._pushPreview()

	def controlTextDidChange_(self, notification):
		if self._isUpdatingControls:
			return
		obj = notification.object()
		if obj in (self._mainGapH, self._mainGapV, self._subGapH, self._subGapV):
			self._normaliseGapLinks()
		self._pushPreview()

	@objc.python_method
	def _syncStepperFromField(self, field, stepper, minimum=1):
		try:
			val = max(minimum, min(999, int(float(field.stringValue() or str(minimum)))))
		except (TypeError, ValueError):
			val = minimum
		self._isUpdatingControls = True
		try:
			field.setStringValue_(str(val))
			stepper.setIntValue_(val)
		finally:
			self._isUpdatingControls = False

	@objc.python_method
	def _pushPreview(self):
		try:
			self.plugin._previewSettings = self._collectSettings()
			Glyphs.redraw()
		except Exception:
			print(traceback.format_exc())

	def ok_(self, sender):
		self._saveFromUI()
		self.plugin._clearPreview()
		self.panel.orderOut_(None)
		self.plugin._loadPrefs()
		Glyphs.redraw()

	def cancel_(self, sender):
		self.plugin._clearPreview()
		self.panel.orderOut_(None)
		Glyphs.redraw()

	def windowWillClose_(self, notification):
		self.plugin._clearPreview()
		Glyphs.redraw()


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
		self._previewSettings = None
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
			main_menu = NSApplication.sharedApplication().mainMenu()
			edit_submenu = main_menu.itemAtIndex_(2).submenu()
			if edit_submenu is not None:
				# Same placement strategy as MasterGrid (Edit menu = item 2, insert index 12)
				edit_submenu.insertItem_atIndex_(settingsItem, 12)
				inserted = True
		except Exception:
			pass
		if not inserted:
			Glyphs.menu[EDIT_MENU].append(settingsItem)

		Glyphs.addCallback(self._drawGrid_, DRAWBACKGROUND)
		Glyphs.addCallback(self._snapDuringDrag_, MOUSEDRAGGED)
		Glyphs.addCallback(self._snapDuringDrag_, MOUSEUP)

		self._installArrowKeyMonitor()

	def _toggleGrid_(self, sender):
		self.gridVisible = not self.gridVisible
		self._showItem.setState_(1 if self.gridVisible else 0)
		Glyphs.defaults[PREF + '.gridVisible'] = self.gridVisible
		Glyphs.redraw()

	def _showSettings_(self, sender):
		self._settingsController.show()

	@objc.python_method
	def _clearPreview(self):
		self._previewSettings = None

	@objc.python_method
	def _effectiveSettings(self, font):
		if getattr(self, '_previewSettings', None) is not None:
			s = self._getSettings(font)
			s.update(self._previewSettings)
			return s
		return self._getSettings(font)

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
			mainGapX, mainGapY, subGapX, subGapY = self._normalisedGapValues(s)

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
					_, _, subGapX, _ = self._normalisedGapValues(s)
					if subGapX > 0.0:
						families = self._triFamilies(orient, stepX, stepY, ySnapOrigin)
						su, sv = self._snapTriangleWithGap(pu, pv, families, subGapX)
					elif orient == 'horizontal':
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
					snappedY = self._nearestGridCoord(pv, ySnapOrigin, mainY, mainGapY, stepY, subGapY)
					u_snapped = self._nearestGridCoord(pu, 0.0, mainX, mainGapX, stepX, subGapX)
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
	def _installArrowKeyMonitor(self):
		"""グリッド表示中、矢印キーをサブグリッド単位、Shift+矢印キーをメイングリッド単位の移動に差し替える。"""
		NSEventMaskKeyDown = 1 << 10

		def handler(event):
			try:
				return self._handleArrowKeyEvent(event)
			except Exception:
				print(traceback.format_exc())
				return event

		self._arrowKeyMonitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
			NSEventMaskKeyDown, handler
		)

	@objc.python_method
	def _handleArrowKeyEvent(self, event):
		if not self.gridVisible:
			return event

		keyCode = event.keyCode()
		# 123=Left, 124=Right, 125=Down, 126=Up
		if keyCode not in (123, 124, 125, 126):
			return event

		SHIFT, CONTROL, OPTION, COMMAND = 1 << 17, 1 << 18, 1 << 19, 1 << 20
		flags = event.modifierFlags() & 0xFFFF0000
		# Shift 単独以外の修飾キー（Cmd/Option/Control）は Glyphs の既定動作に委ねる
		if flags & (CONTROL | OPTION | COMMAND):
			return event

		window = NSApplication.sharedApplication().keyWindow()
		if window is None:
			return event
		# 設定パネルがキーウィンドウのときは横取りしない
		sc = getattr(self, '_settingsController', None)
		if sc is not None:
			panel = getattr(sc, 'panel', None)
			if panel is not None and window is panel:
				return event
		# テキスト編集中（フィールドエディタ）は横取りしない
		responder = window.firstResponder()
		if responder is not None and responder.className() == 'NSTextView':
			return event

		font = Glyphs.font
		if not font:
			return event
		layers = font.selectedLayers
		if not layers:
			return event
		layer = layers[0]

		selectedNodes = [n for n in layer.selection
		                 if hasattr(n, 'position') and hasattr(n, 'type')]
		if not selectedNodes:
			return event

		s = self._getSettings(font)
		mainX, mainY = self._mainIntervals(layer, s)
		if mainX <= 0 or mainY <= 0:
			return event

		if flags & SHIFT:
			stepX, stepY = mainX, mainY
		else:
			stepX, stepY = self._subIntervals(s, mainX, mainY)
			if stepX <= 0 or stepY <= 0:
				stepX, stepY = mainX, mainY
		# ギャップは線の中心を分離するだけなので、矢印移動量は従来の間隔を維持する。

		dx, dy = 0.0, 0.0
		if keyCode == 123:
			dx = -stepX
		elif keyCode == 124:
			dx = stepX
		elif keyCode == 125:
			dy = -stepY
		elif keyCode == 126:
			dy = stepY

		selectedSet = set(selectedNodes)
		moves = {id(n): (n, dx, dy) for n in selectedNodes}
		# オンカーブノードに付随するオフカーブハンドルも一緒に動かす
		for nid, (node, ddx, ddy) in list(moves.items()):
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
				moves[id(neighbor)] = (neighbor, ddx, ddy)

		for node, ddx, ddy in moves.values():
			p = node.position
			node.position = NSPoint(p.x + ddx, p.y + ddy)

		return None

	@objc.python_method
	def _drawGrid_(self, layer, info):
		if not self.gridVisible:
			return
		try:
			width = layer.width
			master = layer.associatedFontMaster()
			yTop = master.ascender if master else 800.0
			yBottom = master.descender if master else -200.0
			try:
				scale = float(info['Scale'])
			except Exception:
				scale = 1.0
			lineWidth = 1.0 / max(scale, 0.01)

			s = self._effectiveSettings(Glyphs.font)
			mainX, mainY = self._mainIntervals(layer, s)
			subX, subY = self._subIntervals(s, mainX, mainY)
			grid_mode = s['mode']

			pivot_y = self._shearPivotY(layer)
			shape = s['gridShape']
			if shape == 'triangle':
				orient = s['triOrientation']
				y_origin = 0.0 if grid_mode == 'unit' else yBottom
				mainGapX, mainGapY, subGapX, subGapY = self._normalisedGapValues(s)
				if subX > 0 and subY > 0:
					self._strokeTriGrid(width, yTop, yBottom, subX, subY, lineWidth, self._colorFromList(s['subColor']), orient, y_origin, layer, pivot_y, subGapX)
				if mainX > 0 and mainY > 0:
					self._strokeTriGrid(width, yTop, yBottom, mainX, mainY, lineWidth, self._colorFromList(s['mainColor']), orient, y_origin, layer, pivot_y, mainGapX)
			else:
				mainGapX, mainGapY, subGapX, subGapY = self._normalisedGapValues(s)
				if subX > 0 and subY > 0:
					self._strokeGrid(width, yTop, yBottom, subX, subY, lineWidth, self._colorFromList(s['subColor']), grid_mode, layer, pivot_y, subGapX, subGapY)
				if mainX > 0 and mainY > 0:
					self._strokeGrid(width, yTop, yBottom, mainX, mainY, lineWidth, self._colorFromList(s['mainColor']), grid_mode, layer, pivot_y, mainGapX, mainGapY)
		except Exception:
			print(traceback.format_exc())

	@objc.python_method
	def _strokeGrid(self, width, yTop, yBottom, stepX, stepY, lineWidth, color, grid_mode, layer, pivot_y, gapX=0.0, gapY=0.0):
		color.set()
		path = NSBezierPath.alloc().init()
		path.setLineWidth_(lineWidth)
		gapX = max(0.0, float(gapX or 0.0))
		gapY = max(0.0, float(gapY or 0.0))

		def offsetsForGap(gap):
			if gap <= 0:
				return (0.0,)
			half = gap * 0.5
			return (-half, half)

		# Draw in glyph coordinate space (straight vertical / horizontal lines).
		# Vertical lines
		u = stepX
		while u < width:
			for offset in offsetsForGap(gapX):
				x = u + offset
				path.moveToPoint_(NSPoint(x, yBottom))
				path.lineToPoint_(NSPoint(x, yTop))
			u += stepX

		# Horizontal lines
		if stepY > 0:
			y_origin = 0.0 if grid_mode == 'unit' else yBottom
			n = int(math.ceil((yBottom - y_origin) / stepY))
			y = y_origin + n * stepY
			while y <= yTop:
				for offset in offsetsForGap(gapY):
					yy = y + offset
					path.moveToPoint_(NSPoint(0.0,   yy))
					path.lineToPoint_(NSPoint(width, yy))
				y += stepY

		# Apply italic shear via Glyphs API (same pivot used by Glyphs itself).
		angle_deg = self._effectiveItalicAngleDegrees(layer)
		if abs(angle_deg) > 0.001:
			path.transformWithAngle_center_(angle_deg, pivot_y)

		path.stroke()

	@objc.python_method
	def _addGapLine(self, path, x0, y0, x1, y1, gap):
		"""Add one line (gap<=0) or two parallel lines offset ±gap/2 along the normal (gap>0)."""
		if gap <= 0.0:
			path.moveToPoint_(NSPoint(x0, y0))
			path.lineToPoint_(NSPoint(x1, y1))
			return
		dx = x1 - x0
		dy = y1 - y0
		L = math.sqrt(dx * dx + dy * dy)
		if L < 1e-12:
			path.moveToPoint_(NSPoint(x0, y0))
			path.lineToPoint_(NSPoint(x1, y1))
			return
		nx = -dy / L
		ny =  dx / L
		half = gap * 0.5
		for sign in (-1.0, 1.0):
			ox = sign * half * nx
			oy = sign * half * ny
			path.moveToPoint_(NSPoint(x0 + ox, y0 + oy))
			path.lineToPoint_(NSPoint(x1 + ox, y1 + oy))

	@objc.python_method
	def _strokeTriGrid(self, width, yTop, yBottom, stepX, stepY, lineWidth, color, orientation, y_origin, layer, pivot_y, gap=0.0):
		if orientation == 'vertical':
			self._strokeTriGridV(width, yTop, yBottom, stepX, stepY, lineWidth, color, y_origin, layer, pivot_y, gap)
		else:
			self._strokeTriGridH(width, yTop, yBottom, stepX, stepY, lineWidth, color, y_origin, layer, pivot_y, gap)

	@objc.python_method
	def _strokeTriGridH(self, width, yTop, yBottom, stepX, stepY, lineWidth, color, y_origin, layer, pivot_y, gap=0.0):
		"""Horizontal tri-grid: horizontal lines + ±diagonal lines (slope = 2*stepY/stepX)."""
		color.set()
		path = NSBezierPath.alloc().init()
		path.setLineWidth_(lineWidth)
		slope = 2.0 * stepY / stepX
		gap = max(0.0, float(gap or 0.0))

		# Horizontal lines, anchored at y_origin
		n_start = int(math.floor((yBottom - y_origin) / stepY))
		n_end = int(math.ceil((yTop - y_origin) / stepY))
		for n in range(n_start, n_end + 1):
			y = y_origin + n * stepY
			if yBottom <= y <= yTop:
				self._addGapLine(path, 0.0, y, width, y, gap)

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
				self._addGapLine(path, x0, yBottom, x1, yTop, gap)
			# "\"
			x0b = m * stepX - (yBottom - y_origin) / slope
			x1b = m * stepX - (yTop - y_origin) / slope
			if not (x1b > width or x0b < 0):
				self._addGapLine(path, x0b, yBottom, x1b, yTop, gap)

		angle_deg = self._effectiveItalicAngleDegrees(layer)
		if abs(angle_deg) > 0.001:
			path.transformWithAngle_center_(angle_deg, pivot_y)
		path.stroke()

	@objc.python_method
	def _strokeTriGridV(self, width, yTop, yBottom, stepX, stepY, lineWidth, color, y_origin, layer, pivot_y, gap=0.0):
		"""Vertical tri-grid: vertical lines + ±diagonal lines (slope = stepY/(2*stepX))."""
		color.set()
		path = NSBezierPath.alloc().init()
		path.setLineWidth_(lineWidth)
		slope_v = stepY / (2.0 * stepX)
		gap = max(0.0, float(gap or 0.0))

		# Vertical lines
		u = stepX
		while u < width:
			self._addGapLine(path, u, yBottom, u, yTop, gap)
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
				self._addGapLine(path, 0.0, y_x0, width, y_xW, gap)
			# "\"
			y_x0b = base_y
			y_xWb = -slope_v * width + base_y
			y_lo2, y_hi2 = min(y_x0b, y_xWb), max(y_x0b, y_xWb)
			if not (y_hi2 < yBottom or y_lo2 > yTop):
				self._addGapLine(path, 0.0, y_x0b, width, y_xWb, gap)

		angle_deg = self._effectiveItalicAngleDegrees(layer)
		if abs(angle_deg) > 0.001:
			path.transformWithAngle_center_(angle_deg, pivot_y)
		path.stroke()

	@objc.python_method
	def _floatSetting(self, s, key, default=0.0):
		try:
			return float(s.get(key, default))
		except (TypeError, ValueError):
			return float(default)

	@objc.python_method
	def _normalisedGapValues(self, s, include_disabled=False):
		mainGapX = max(0.0, self._floatSetting(s, 'mainGapX', 0.0))
		mainGapY = max(0.0, self._floatSetting(s, 'mainGapY', 0.0))
		subGapX = max(0.0, self._floatSetting(s, 'subGapX', 0.0))
		subGapY = max(0.0, self._floatSetting(s, 'subGapY', 0.0))
		if s.get('gapSyncHV', False):
			mainGapY = mainGapX
			subGapY = subGapX
		if s.get('gapSyncMainSub', False):
			subGapX = mainGapX
			subGapY = mainGapY
		if include_disabled:
			return mainGapX, mainGapY, subGapX, subGapY
		if not s.get('gapEnabled', False):
			return 0.0, 0.0, 0.0, 0.0
		return mainGapX, mainGapY, subGapX, subGapY

	@objc.python_method
	def _gapOffsets(self, gap):
		gap = max(0.0, float(gap or 0.0))
		if gap <= 0.0:
			return (0.0,)
		half = gap * 0.5
		return (-half, half)

	@objc.python_method
	def _nearestGridCoord(self, value, origin, mainStep, mainGap, subStep, subGap):
		best = None
		for step, gap in ((mainStep, mainGap), (subStep, subGap)):
			if step <= 0:
				continue
			for offset in self._gapOffsets(gap):
				k = round((value - origin - offset) / step)
				candidate = origin + k * step + offset
				distance = abs(candidate - value)
				if best is None or distance < best[0]:
					best = (distance, candidate)
		return best[1] if best is not None else value

	@objc.python_method
	def _triFamilies(self, orient, stepX, stepY, O_y):
		"""Return 3 line families as (ux, uy, spacing, phase) for a tri-grid.

		Each family is defined by its unit normal (ux, uy) and the series
		  t = phase + k * spacing  (k integer)
		where t = ux*x + uy*y is the projection of a point onto the normal.
		Gap-offset lines lie at t = phase + k*spacing ± gap/2.
		"""
		if orient == 'horizontal':
			slope = 2.0 * stepY / stepX          # slope of diagonal lines
			sq = math.sqrt(1.0 + slope * slope)
			return [
				# horizontal lines: normal (0,1), phase = O_y, spacing = stepY
				(0.0,        1.0,       stepY,             O_y),
				# "/" lines: using normal (slope, -1)/sq so t increases with m
				(slope / sq, -1.0 / sq, slope * stepX / sq, -O_y / sq),
				# "\" lines: normal (slope, 1)/sq, phase = O_y/sq
				(slope / sq,  1.0 / sq, slope * stepX / sq,  O_y / sq),
			]
		else:  # vertical
			slope_v = stepY / (2.0 * stepX)      # slope of diagonal lines
			sq_v = math.sqrt(1.0 + slope_v * slope_v)
			return [
				# vertical lines: normal (1,0), phase = 0, spacing = stepX
				(1.0,              0.0,        stepX,         0.0),
				# "/" lines: normal (-slope_v, 1)/sq_v, phase = O_y/sq_v
				(-slope_v / sq_v,  1.0 / sq_v, stepY / sq_v,  O_y / sq_v),
				# "\" lines: normal (slope_v, 1)/sq_v, phase = O_y/sq_v
				( slope_v / sq_v,  1.0 / sq_v, stepY / sq_v,  O_y / sq_v),
			]

	@objc.python_method
	def _nearestLineValue(self, t, phase, spacing, gap):
		"""Return the value (from the series phase+k*spacing ± gap/2) nearest to t."""
		if spacing <= 0:
			return t
		k0 = round((t - phase) / spacing)
		best = None
		for dk in (-1, 0, 1):
			base = phase + (k0 + dk) * spacing
			offsets = (-gap * 0.5, gap * 0.5) if gap > 0.0 else (0.0,)
			for off in offsets:
				val = base + off
				d = abs(val - t)
				if best is None or d < best[0]:
					best = (d, val)
		return best[1] if best is not None else t

	@objc.python_method
	def _snapTriangleWithGap(self, pu, pv, families, gap):
		"""Snap (pu,pv) to the nearest intersection of gap-offset triangle lines.

		For each of the 3 families finds the nearest line (including ±gap/2 offset),
		then tries all 3 pairs of families and returns the intersection closest to P.
		"""
		ws = []
		for ux, uy, spacing, phase in families:
			t = ux * pu + uy * pv
			ws.append(self._nearestLineValue(t, phase, spacing, gap))

		best = None
		for i, j in ((0, 1), (0, 2), (1, 2)):
			uxi, uyi = families[i][0], families[i][1]
			uxj, uyj = families[j][0], families[j][1]
			det = uxi * uyj - uyi * uxj
			if abs(det) < 1e-12:
				continue
			x = (ws[i] * uyj - ws[j] * uyi) / det
			y = (uxi * ws[j] - uxj * ws[i]) / det
			d2 = (x - pu) ** 2 + (y - pv) ** 2
			if best is None or d2 < best[0]:
				best = (d2, x, y)

		if best is None:
			return pu, pv
		return best[1], best[2]

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
			'gapEnabled':     False,
			'mainGapX':       0.0,
			'mainGapY':       0.0,
			'subGapX':        0.0,
			'subGapY':        0.0,
			'gapSyncHV':      False,
			'gapSyncMainSub': False,
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
			'gapEnabled':     bool(d.get(p + '.gapEnabled', False)),
			'mainGapX':       float(d.get(p + '.mainGapX', 0.0)),
			'mainGapY':       float(d.get(p + '.mainGapY', 0.0)),
			'subGapX':        float(d.get(p + '.subGapX', 0.0)),
			'subGapY':        float(d.get(p + '.subGapY', 0.0)),
			'gapSyncHV':      bool(d.get(p + '.gapSyncHV', False)),
			'gapSyncMainSub': bool(d.get(p + '.gapSyncMainSub', False)),
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
		d[p + '.gapEnabled']     = s.get('gapEnabled', False)
		d[p + '.mainGapX']       = s.get('mainGapX', 0.0)
		d[p + '.mainGapY']       = s.get('mainGapY', 0.0)
		d[p + '.subGapX']        = s.get('subGapX', 0.0)
		d[p + '.subGapY']        = s.get('subGapY', 0.0)
		d[p + '.gapSyncHV']      = s.get('gapSyncHV', False)
		d[p + '.gapSyncMainSub'] = s.get('gapSyncMainSub', False)

	@objc.python_method
	def _loadPrefs(self):
		self.gridVisible = bool(Glyphs.defaults.get(PREF + '.gridVisible', True))

	@objc.python_method
	def __file__(self):
		return __file__

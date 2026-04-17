# encoding: utf-8
from __future__ import division, print_function, unicode_literals
import objc
import traceback
from GlyphsApp import Glyphs, EDIT_MENU, VIEW_MENU, DRAWBACKGROUND, MOUSEDRAGGED, MOUSEUP, OFFCURVE
from GlyphsApp.plugins import GeneralPlugin
from AppKit import (
	NSMenuItem, NSColor, NSBezierPath, NSPoint,
	NSPanel, NSBox, NSTextField, NSStepper, NSButton, NSColorWell,
	NSMakeRect, NSFont,
	NSTitledWindowMask, NSClosableWindowMask, NSFloatingWindowLevel,
	NSBackingStoreBuffered,
)
from Foundation import NSObject, NSNotificationCenter

PREF = 'com.palf.SnappingGrid'

# ─────────────────────────────────────────────
# Settings panel
# ─────────────────────────────────────────────

PANEL_W = 420
PANEL_H = 380


def _label(text, x, y, w, h):
	f = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
	f.setStringValue_(text)
	f.setBezeled_(False)
	f.setDrawsBackground_(False)
	f.setEditable_(False)
	f.setSelectable_(False)
	f.setFont_(NSFont.systemFontOfSize_(12))
	return f


def _field(x, y, w=60, h=22):
	f = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
	f.setBezeled_(True)
	f.setEditable_(True)
	f.setFont_(NSFont.systemFontOfSize_(12))
	return f


def _stepper(x, y, minVal=1, maxVal=999, increment=1):
	s = NSStepper.alloc().initWithFrame_(NSMakeRect(x, y, 19, 22))
	s.setMinValue_(minVal)
	s.setMaxValue_(maxVal)
	s.setIncrement_(increment)
	s.setValueWraps_(False)
	return s


def _checkbox(text, x, y, w=120, h=18):
	b = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
	b.setButtonType_(3)  # NSSwitchButton
	b.setTitle_(text)
	b.setFont_(NSFont.systemFontOfSize_(12))
	return b


def _radio(text, x, y, w=100, h=18):
	b = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
	b.setButtonType_(4)  # NSRadioButton
	b.setTitle_(text)
	b.setFont_(NSFont.systemFontOfSize_(12))
	return b


def _colorWell(x, y, w=44, h=26):
	cw = NSColorWell.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
	return cw


def _separator(y, w=PANEL_W - 40):
	box = NSBox.alloc().initWithFrame_(NSMakeRect(20, y, w, 1))
	box.setBoxType_(2)  # NSBoxSeparator
	return box


class SettingsPanelController(NSObject):

	def initWithPlugin_(self, plugin):
		self = objc.super(SettingsPanelController, self).init()
		if self is None:
			return None
		self.plugin = plugin
		self.panel = None
		return self

	def show(self):
		if self.panel is None:
			self._build()
		self._loadToUI()
		self.panel.makeKeyAndOrderFront_(None)

	def _build(self):
		lx = Glyphs.localize
		mask = NSTitledWindowMask | NSClosableWindowMask
		panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
			NSMakeRect(0, 0, PANEL_W, PANEL_H),
			mask,
			NSBackingStoreBuffered,
			False,
		)
		panel.setTitle_(lx({'en': 'Snapping Grid Settings', 'ja': 'スナッピンググリッドの設定',
		                     'zh': '吸附网格设置', 'ko': '스냅 그리드 설정'}))
		panel.setLevel_(NSFloatingWindowLevel)
		panel.center()

		cv = panel.contentView()

		# ── Row: grid mode ──────────────────────────── y=330
		cv.addSubview_(_label(lx({'en': 'Grid Mode:', 'ja': 'グリッド方式:', 'zh': '网格方式:', 'ko': '그리드 방식:'}),
		                      20, 338, 100, 20))
		self._radioDivision = _radio(lx({'en': 'Division', 'ja': '分割数', 'zh': '分割数', 'ko': '분할 수'}),
		                             125, 337, 90, 20)
		self._radioUnit = _radio(lx({'en': 'Unit', 'ja': 'Unit数', 'zh': 'Unit数', 'ko': 'Unit 수'}),
		                         220, 337, 80, 20)
		self._radioDivision.setTarget_(self)
		self._radioDivision.setAction_('modeChanged_')
		self._radioUnit.setTarget_(self)
		self._radioUnit.setAction_('modeChanged_')
		cv.addSubview_(self._radioDivision)
		cv.addSubview_(self._radioUnit)

		cv.addSubview_(_separator(322))

		# ── Main Grid ─────────────────────────────── y=290–305
		cv.addSubview_(_label(lx({'en': 'Main Grid', 'ja': 'メイングリッド', 'zh': '主网格', 'ko': '메인 그리드'}),
		                      20, 305, 120, 20))
		cv.addSubview_(_label('H:', 20, 278, 20, 22))
		self._mainH = _field(40, 278)
		self._mainHStep = _stepper(102, 278)
		cv.addSubview_(self._mainH)
		cv.addSubview_(self._mainHStep)

		cv.addSubview_(_label('V:', 145, 278, 20, 22))
		self._mainV = _field(165, 278)
		self._mainVStep = _stepper(227, 278)
		cv.addSubview_(self._mainV)
		cv.addSubview_(self._mainVStep)

		self._mainSync = _checkbox(lx({'en': 'Sync H/V', 'ja': '縦横同期', 'zh': '同步H/V', 'ko': 'H/V 동기화'}),
		                           270, 279, 110, 18)
		cv.addSubview_(self._mainSync)

		cv.addSubview_(_separator(260))

		# ── Sub Grid ──────────────────────────────── y=225–245
		cv.addSubview_(_label(lx({'en': 'Sub Grid (main subdivisions)', 'ja': 'サブグリッド（メインの分割数）',
		                          'zh': '子网格（主网格分割数）', 'ko': '서브 그리드（메인 분할 수）'}),
		                      20, 245, 280, 20))
		cv.addSubview_(_label('H:', 20, 218, 20, 22))
		self._subH = _field(40, 218)
		self._subHStep = _stepper(102, 218)
		cv.addSubview_(self._subH)
		cv.addSubview_(self._subHStep)

		cv.addSubview_(_label('V:', 145, 218, 20, 22))
		self._subV = _field(165, 218)
		self._subVStep = _stepper(227, 218)
		cv.addSubview_(self._subV)
		cv.addSubview_(self._subVStep)

		self._subSync = _checkbox(lx({'en': 'Sync H/V', 'ja': '縦横同期', 'zh': '同步H/V', 'ko': 'H/V 동기화'}),
		                          270, 219, 110, 18)
		cv.addSubview_(self._subSync)

		cv.addSubview_(_separator(200))

		# ── Colors ───────────────────────────────── y=160–185
		cv.addSubview_(_label(lx({'en': 'Main Color:', 'ja': 'メイン色:', 'zh': '主色:', 'ko': '메인 색상:'}),
		                      20, 175, 85, 20))
		self._mainColorWell = _colorWell(108, 170)
		cv.addSubview_(self._mainColorWell)

		cv.addSubview_(_label(lx({'en': 'Sub Color:', 'ja': 'サブ色:', 'zh': '子色:', 'ko': '서브 색상:'}),
		                      220, 175, 75, 20))
		self._subColorWell = _colorWell(298, 170)
		cv.addSubview_(self._subColorWell)

		cv.addSubview_(_separator(155))

		# ── Snap toggle ──────────────────────────── y=125
		self._snapCheck = _checkbox(lx({'en': 'Enable snap', 'ja': 'スナップを有効にする',
		                                'zh': '启用吸附', 'ko': '스냅 활성화'}),
		                            20, 128, 200, 18)
		cv.addSubview_(self._snapCheck)

		cv.addSubview_(_separator(110))

		# ── Buttons ──────────────────────────────── y=20
		cancelBtn = NSButton.alloc().initWithFrame_(NSMakeRect(PANEL_W - 200, 20, 85, 28))
		cancelBtn.setTitle_(lx({'en': 'Cancel', 'ja': 'キャンセル', 'zh': '取消', 'ko': '취소'}))
		cancelBtn.setBezelStyle_(1)  # NSRoundedBezelStyle
		cancelBtn.setTarget_(self)
		cancelBtn.setAction_('cancel_')
		cv.addSubview_(cancelBtn)

		okBtn = NSButton.alloc().initWithFrame_(NSMakeRect(PANEL_W - 105, 20, 85, 28))
		okBtn.setTitle_(lx({'en': 'OK', 'ja': 'OK', 'zh': 'OK', 'ko': 'OK'}))
		okBtn.setBezelStyle_(1)
		okBtn.setKeyEquivalent_('\r')
		okBtn.setTarget_(self)
		okBtn.setAction_('ok_')
		cv.addSubview_(okBtn)

		# Wire steppers ↔ text fields
		for step, field in ((self._mainHStep, self._mainH), (self._mainVStep, self._mainV),
		                    (self._subHStep, self._subH), (self._subVStep, self._subV)):
			step.setTarget_(self)
			step.setAction_('stepperChanged_')
		for field in (self._mainH, self._mainV, self._subH, self._subV):
			field.setDelegate_(self)

		self._stepperMap = {
			id(self._mainHStep): self._mainH, id(self._mainVStep): self._mainV,
			id(self._subHStep): self._subH,  id(self._subVStep): self._subV,
		}

		self.panel = panel

	def _loadToUI(self):
		p = PREF
		d = Glyphs.defaults
		mode = d.get(p + '.mode', 'division')
		self._radioDivision.setState_(1 if mode == 'division' else 0)
		self._radioUnit.setState_(1 if mode == 'unit' else 0)

		if mode == 'unit':
			self._mainH.setStringValue_(str(int(d.get(p + '.mainUnitX', 100))))
			self._mainV.setStringValue_(str(int(d.get(p + '.mainUnitY', 100))))
			self._mainHStep.setIntValue_(int(d.get(p + '.mainUnitX', 100)))
			self._mainVStep.setIntValue_(int(d.get(p + '.mainUnitY', 100)))
		else:
			self._mainH.setStringValue_(str(int(d.get(p + '.mainDivX', 4))))
			self._mainV.setStringValue_(str(int(d.get(p + '.mainDivY', 4))))
			self._mainHStep.setIntValue_(int(d.get(p + '.mainDivX', 4)))
			self._mainVStep.setIntValue_(int(d.get(p + '.mainDivY', 4)))

		self._mainSync.setState_(1 if d.get(p + '.mainSync', False) else 0)
		self._subH.setStringValue_(str(int(d.get(p + '.subDivX', 2))))
		self._subV.setStringValue_(str(int(d.get(p + '.subDivY', 2))))
		self._subHStep.setIntValue_(int(d.get(p + '.subDivX', 2)))
		self._subVStep.setIntValue_(int(d.get(p + '.subDivY', 2)))
		self._subSync.setState_(1 if d.get(p + '.subSync', False) else 0)

		self._mainColorWell.setColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(
			float(d.get(p + '.mainR', 0.2)), float(d.get(p + '.mainG', 0.5)),
			float(d.get(p + '.mainB', 1.0)), float(d.get(p + '.mainA', 0.4))))
		self._subColorWell.setColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(
			float(d.get(p + '.subR', 0.2)), float(d.get(p + '.subG', 0.5)),
			float(d.get(p + '.subB', 1.0)), float(d.get(p + '.subA', 0.15))))

		self._snapCheck.setState_(1 if d.get(p + '.snapEnabled', True) else 0)

	def _saveFromUI(self):
		p = PREF
		d = Glyphs.defaults
		mode = 'division' if self._radioDivision.state() == 1 else 'unit'
		d[p + '.mode'] = mode
		hVal = max(1, int(float(self._mainH.stringValue() or '1')))
		vVal = max(1, int(float(self._mainV.stringValue() or '1')))
		if mode == 'unit':
			d[p + '.mainUnitX'] = hVal
			d[p + '.mainUnitY'] = vVal
		else:
			d[p + '.mainDivX'] = hVal
			d[p + '.mainDivY'] = vVal
		d[p + '.mainSync'] = (self._mainSync.state() == 1)

		d[p + '.subDivX'] = max(1, int(float(self._subH.stringValue() or '1')))
		d[p + '.subDivY'] = max(1, int(float(self._subV.stringValue() or '1')))
		d[p + '.subSync'] = (self._subSync.state() == 1)

		mc = self._mainColorWell.color().colorUsingColorSpaceName_('NSCalibratedRGBColorSpace')
		sc = self._subColorWell.color().colorUsingColorSpaceName_('NSCalibratedRGBColorSpace')
		if mc:
			d[p + '.mainR'] = mc.redComponent()
			d[p + '.mainG'] = mc.greenComponent()
			d[p + '.mainB'] = mc.blueComponent()
			d[p + '.mainA'] = mc.alphaComponent()
		if sc:
			d[p + '.subR'] = sc.redComponent()
			d[p + '.subG'] = sc.greenComponent()
			d[p + '.subB'] = sc.blueComponent()
			d[p + '.subA'] = sc.alphaComponent()

		d[p + '.snapEnabled'] = (self._snapCheck.state() == 1)

	def modeChanged_(self, sender):
		pass  # radio state updates automatically

	def stepperChanged_(self, sender):
		field = self._stepperMap.get(id(sender))
		if field:
			val = int(sender.intValue())
			field.setStringValue_(str(val))
			# Sync paired field if needed
			isMain = (sender is self._mainHStep or sender is self._mainVStep)
			isH = (sender is self._mainHStep or sender is self._subHStep)
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
		if not self.snapEnabled:
			return
		try:
			font = Glyphs.font
			if not font:
				return
			layers = font.selectedLayers
			if not layers:
				return
			layer = layers[0]
			mainX, mainY = self._mainIntervals(layer)
			if mainX <= 0 or mainY <= 0:
				return

			master = layer.associatedFontMaster()
			yBottom = master.descender if master else -200.0

			# Only operate on GSNode items (skip anchors, components)
			selectedNodes = [n for n in layer.selection
			                 if hasattr(n, 'position') and hasattr(n, 'type')]
			if not selectedNodes:
				return
			selectedSet = set(selectedNodes)

			# Compute snap delta for each selected node (snap grid aligned to yBottom)
			moves = {}
			for node in selectedNodes:
				pos = node.position
				snappedX = round(pos.x / mainX) * mainX
				snappedY = round((pos.y - yBottom) / mainY) * mainY + yBottom
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

			mainX, mainY = self._mainIntervals(layer)
			subX, subY = self._subIntervals(mainX, mainY)

			if subX > 0 and subY > 0:
				self._strokeGrid(width, yTop, yBottom, subX, subY, lineWidth, self._subColor())
			if mainX > 0 and mainY > 0:
				self._strokeGrid(width, yTop, yBottom, mainX, mainY, lineWidth, self._mainColor())
		except Exception:
			print(traceback.format_exc())

	@objc.python_method
	def _strokeGrid(self, width, yTop, yBottom, stepX, stepY, lineWidth, color):
		color.set()
		path = NSBezierPath.alloc().init()
		path.setLineWidth_(lineWidth)
		x = stepX
		while x < width:
			path.moveToPoint_(NSPoint(x, yBottom))
			path.lineToPoint_(NSPoint(x, yTop))
			x += stepX
		y = yBottom + stepY
		while y < yTop:
			path.moveToPoint_(NSPoint(0, y))
			path.lineToPoint_(NSPoint(width, y))
			y += stepY
		path.stroke()

	@objc.python_method
	def _mainIntervals(self, layer):
		mode = Glyphs.defaults.get(PREF + '.mode', 'division')
		if mode == 'unit':
			x = float(Glyphs.defaults.get(PREF + '.mainUnitX', 100))
			y = float(Glyphs.defaults.get(PREF + '.mainUnitY', 100))
		else:
			divX = max(1, int(Glyphs.defaults.get(PREF + '.mainDivX', 4)))
			divY = max(1, int(Glyphs.defaults.get(PREF + '.mainDivY', 4)))
			master = layer.associatedFontMaster()
			height = (master.ascender - master.descender) if master else 1000.0
			x = layer.width / divX
			y = height / divY
		return x, y

	@objc.python_method
	def _subIntervals(self, mainX, mainY):
		subDivX = max(1, int(Glyphs.defaults.get(PREF + '.subDivX', 2)))
		subDivY = max(1, int(Glyphs.defaults.get(PREF + '.subDivY', 2)))
		return mainX / subDivX, mainY / subDivY

	@objc.python_method
	def _mainColor(self):
		d = Glyphs.defaults
		return NSColor.colorWithCalibratedRed_green_blue_alpha_(
			float(d.get(PREF + '.mainR', 0.2)), float(d.get(PREF + '.mainG', 0.5)),
			float(d.get(PREF + '.mainB', 1.0)), float(d.get(PREF + '.mainA', 0.4)))

	@objc.python_method
	def _subColor(self):
		d = Glyphs.defaults
		return NSColor.colorWithCalibratedRed_green_blue_alpha_(
			float(d.get(PREF + '.subR', 0.2)), float(d.get(PREF + '.subG', 0.5)),
			float(d.get(PREF + '.subB', 1.0)), float(d.get(PREF + '.subA', 0.15)))

	@objc.python_method
	def _loadPrefs(self):
		self.gridVisible = bool(Glyphs.defaults.get(PREF + '.gridVisible', True))
		self.snapEnabled = bool(Glyphs.defaults.get(PREF + '.snapEnabled', True))

	@objc.python_method
	def __file__(self):
		return __file__

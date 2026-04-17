# encoding: utf-8
from __future__ import division, print_function, unicode_literals
import objc
import traceback
from GlyphsApp import Glyphs, EDIT_MENU, VIEW_MENU, DRAWBACKGROUND
from GlyphsApp.plugins import GeneralPlugin
from AppKit import NSMenuItem, NSColor, NSBezierPath, NSPoint

PREF = 'com.palf.SnappingGrid'


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

		# View menu: show/hide grid
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

		# Edit menu: settings
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

	def _toggleGrid_(self, sender):
		self.gridVisible = not self.gridVisible
		self._showItem.setState_(1 if self.gridVisible else 0)
		Glyphs.defaults[PREF + '.gridVisible'] = self.gridVisible
		Glyphs.redraw()

	def _showSettings_(self, sender):
		pass  # Phase 3

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
		r = float(Glyphs.defaults.get(PREF + '.mainR', 0.2))
		g = float(Glyphs.defaults.get(PREF + '.mainG', 0.5))
		b = float(Glyphs.defaults.get(PREF + '.mainB', 1.0))
		a = float(Glyphs.defaults.get(PREF + '.mainA', 0.4))
		return NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)

	@objc.python_method
	def _subColor(self):
		r = float(Glyphs.defaults.get(PREF + '.subR', 0.2))
		g = float(Glyphs.defaults.get(PREF + '.subG', 0.5))
		b = float(Glyphs.defaults.get(PREF + '.subB', 1.0))
		a = float(Glyphs.defaults.get(PREF + '.subA', 0.15))
		return NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)

	@objc.python_method
	def _loadPrefs(self):
		self.gridVisible = bool(Glyphs.defaults.get(PREF + '.gridVisible', True))
		self.snapEnabled = bool(Glyphs.defaults.get(PREF + '.snapEnabled', True))

	@objc.python_method
	def __file__(self):
		return __file__

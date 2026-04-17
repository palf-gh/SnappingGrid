# encoding: utf-8
from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import Glyphs, EDIT_MENU
from GlyphsApp.plugins import GeneralPlugin
from AppKit import NSMenuItem


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
		pass

	@objc.python_method
	def __file__(self):
		return __file__

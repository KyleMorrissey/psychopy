# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from os import path
from .._base import BaseVisualComponent, Param, getInitVals, _translate

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'text.png')
tooltip = _translate('Text: present text stimuli')

# only use _localized values for label values, nothing functional:
_localized = {'text': _translate('Text'),
              'font': _translate('Font'),
              'letterHeight': _translate('Letter height'),
              'wrapWidth': _translate('Wrap width'),
              'flip': _translate('Flip (mirror)')}


class TextComponent(BaseVisualComponent):
    """An event class for presenting text-based stimuli
    """
    categories = ['Stimuli']
    targets = ['PsychoPy', 'PsychoJS']

    def __init__(self, exp, parentName, name='text',
                 # effectively just a display-value
                 text=_translate('Any text\n\nincluding line breaks'),
                 font='Arial', units='from exp settings',
                 color='white', colorSpace='rgb',
                 pos=(0, 0), letterHeight=0.1, ori=0,
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 flip='', startEstim='', durationEstim='', wrapWidth=''):
        super(TextComponent, self).__init__(exp, parentName, name=name,
                                            units=units,
                                            color=color,
                                            colorSpace=colorSpace,
                                            pos=pos,
                                            ori=ori,
                                            startType=startType,
                                            startVal=startVal,
                                            stopType=stopType,
                                            stopVal=stopVal,
                                            startEstim=startEstim,
                                            durationEstim=durationEstim)
        self.type = 'Text'
        self.url = "http://www.psychopy.org/builder/components/text.html"

        # params
        _allow3 = ['constant', 'set every repeat', 'set every frame']  # list
        self.params['text'] = Param(
            text, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],  # copy the list
            hint=_translate("The text to be displayed"),
            label=_localized['text'])
        self.params['font'] = Param(
            font, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],  # copy the list
            hint=_translate("The font name (e.g. Comic Sans)"),
            label=_localized['font'])
        del self.params['size']  # because you can't specify width for text
        self.params['letterHeight'] = Param(
            letterHeight, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],  # copy the list
            hint=_translate("Specifies the height of the letter (the width"
                            " is then determined by the font)"),
            label=_localized['letterHeight'])

        self.params['wrapWidth'] = Param(
            wrapWidth, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant'],
            hint=_translate("How wide should the text get when it wraps? (in"
                            " the specified units)"),
            label=_localized['wrapWidth'])
        self.params['flip'] = Param(
            flip, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],  # copy the list
            hint=_translate("horiz = left-right reversed; vert = up-down"
                            " reversed; $var = variable"),
            label=_localized['flip'])
        for prm in ('ori', 'opacity', 'colorSpace', 'units', 'wrapWidth',
                    'flip'):
            self.params[prm].categ = 'Advanced'

    def writeInitCode(self, buff):
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        else:
            unitsStr = "units=%(units)s, " % self.params
        # do writing of init
        # replaces variable params with sensible defaults
        inits = getInitVals(self.params)
        if self.params['wrapWidth'].val in ['', 'None', 'none']:
            inits['wrapWidth'] = 'None'
        code = ("%(name)s = visual.TextStim(win=win, "
                "name='%(name)s',\n"
                "    text=%(text)s,\n"
                "    font=%(font)s,\n"
                "    " + unitsStr +
                "pos=%(pos)s, height=%(letterHeight)s, "
                "wrapWidth=%(wrapWidth)s, ori=%(ori)s, \n"
                "    color=%(color)s, colorSpace=%(colorSpace)s, "
                "opacity=%(opacity)s,")
        buff.writeIndentedLines(code % inits)
        flip = self.params['flip'].val.strip()
        if flip == 'horiz':
            flipStr = 'flipHoriz=True, '
        elif flip == 'vert':
            flipStr = 'flipVert=True, '
        elif flip:
            msg = ("flip value should be 'horiz' or 'vert' (no quotes)"
                   " in component '%s'")
            raise ValueError(msg % self.params['name'].val)
        else:
            flipStr = ''
        depth = -self.getPosInRoutine()
        buff.writeIndented('    ' + flipStr + 'depth=%.1f);\n' % depth)

    def writeInitCodeJS(self, buff):        
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        else:
            unitsStr = "units:'%(units)s', " % self.params
        # do writing of init
        # replaces variable params with sensible defaults
        inits = getInitVals(self.params)
        if self.params['wrapWidth'].val in ['', 'None', 'none']:
            inits['wrapWidth'] = 'undefined'
        code = ("%(name)s = new psychoJS.visual.TextStim({win : win, "
                "name : '%(name)s',\n"
                "    text : %(text)s,\n"
                "    font : %(font)s,\n"
                "    " + unitsStr +
                "pos : %(pos)s, height : %(letterHeight)s, "
                "wrapWidth : %(wrapWidth)s, ori:%(ori)s, \n"
                "    color : %(color)s, colorSpace:%(colorSpace)s, "
                "opacity : %(opacity)s,")
        buff.writeIndentedLines(code % inits)
        flip = self.params['flip'].val.strip()
        if flip == 'horiz':
            flipStr = 'flipHoriz : true, '
        elif flip == 'vert':
            flipStr = 'flipVert : true, '
        elif flip:
            msg = ("flip value should be 'horiz' or 'vert' (no quotes)"
                   " in component '%s'")
            raise ValueError(msg % self.params['name'].val)
        else:
            flipStr = ''
        depth = -self.getPosInRoutine()
        code = ("    %sdepth : %.1f \n"
                            "});\n" % (flipStr, depth)
                            )
        buff.writeIndentedLines(code)

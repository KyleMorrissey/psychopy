# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import

import time
import wx
from wx.lib import scrolledpanel
from wx import dataview
from wx import richtext

try:
    import pyosf
    havePyosf = True
except:
    havePyosf = False
from . import wxIDs
from psychopy import logging, web
from psychopy.app import dialogs
from HTMLParser import HTMLParser

class ProjectsMenu(wx.Menu):
    _user = None
    app = None
    searchDlg = None

    @classmethod
    def setUser(self, user):
        """
        a classmethod allowing all instances of this class to update their username
        lists in the submenu

        Parameters
        ----------
        user : str
            OSF username (email address) of the user

        """
        self._user = user
        self.app.osf_session = pyosf.Session(user)
        if self.searchDlg is not None:
            self.searchDlg.updateUserProjs()

    def __init__(self, parent):
        wx.Menu.__init__(self)
        self.parent = parent
        ProjectsMenu.app = parent.app
        keys = self.app.keys

        if self.app.osf_session is None:
            # create a default (anonymous) session with osf
            self.app.osf_session = pyosf.Session()

        self.Append(wxIDs.projsAbout, "Tell me more...")
        if not havePyosf:
            self.Append(wx.NewId(), "Requires pyosf (not installed)")
            self.knownUsers = {}
        else:
            self.knownUsers = pyosf.TokenStorage()  # a dict of name:token
        self.userMenu = wx.Menu()  # a sub-menu for usernames and login
        for name in self.knownUsers:
            self.addUserToSubMenu(name)
        self.userMenu.AppendSeparator()
        self.userMenu.Append(wxIDs.projsNewUser, "Log in...\t{}".format(keys['projectsLogIn']))
        wx.EVT_MENU(parent, wxIDs.projsNewUser,  self.onLogIn)

        wx.EVT_MENU(parent, wxIDs.projsAbout,  self.onAbout)
        self.AppendSubMenu(self.userMenu, "User")
        self.Append(wxIDs.projsSearch, "Search OSF\t{}".format(keys['projectFind']))
        wx.EVT_MENU(parent, wxIDs.projsSearch,  self.onSearch)
        self.Append(wxIDs.projsSync, "Sync\t{}".format(keys['projectsSync']))
        wx.EVT_MENU(parent, wxIDs.projsSync,  self.onSync)

    def addUserToSubMenu(self, username):
        thisId = wx.NewId()
        self.userMenu.Append(thisId, username)
        wx.EVT_MENU(self.parent, thisId,  self.onSetUser)

    def onAbout(self, event):
        logging.info("")
        pass  # TODO: go to web page

    def onSetUser(self, event):
        """NB. this is used by the wx menu event. It then calls self.setUser(username)
        which is a classmethod allowing all instances of this class to update
        their username lists in the submenu
        """
        self.setUser(self.userMenu.GetLabelText(event.GetId()))

    def onSync(self, event):
        logging.info("")
        pass  # TODO: project sync and enable/disable

    def onSearch(self, event):
        ProjectsMenu.searchDlg = SearchDlg(app=self.parent.app)
        ProjectsMenu.searchDlg.Show()

    def onLogIn(self, event):
        dlg = LogInDlg(app=self.app)
        dlg.Show()


class LogInDlg(wx.Dialog):
    defaultStyle = (wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT |
                    wx.TAB_TRAVERSAL | wx.RESIZE_BORDER)

    def __init__(self, app, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=defaultStyle):
        wx.Dialog.__init__(self, None, title="Log in to Open Science Framework")
        self.session = app.osf_session

        self.fieldsSizer = wx.GridBagSizer(vgap=5, hgap=5)

        if web.haveInternetAccess():
            self.status = wx.StaticText(self, label="Status: Ready")
        else:
            self.status = wx.StaticText(self, label="No internet access")
        self.fieldsSizer.Add(self.status,
                             pos=(0, 0), span=(1, 2),
                             flag=wx.ALIGN_CENTER, border=10)

        # user info
        self.fieldsSizer.Add(wx.StaticText(self, label="OSF Username (email)"),
                             pos=(1, 0), flag=wx.ALIGN_RIGHT)
        self.username = wx.TextCtrl(self)
        self.username.SetToolTipString("Your username on OSF "
                                       "(the email address you used)")
        self.fieldsSizer.Add(self.username,
                             pos=(1, 1), flag=wx.ALIGN_LEFT)
        # pass info
        self.fieldsSizer.Add(wx.StaticText(self, label="Password"),
                             pos=(2, 0), flag=wx.ALIGN_RIGHT)
        self.password = wx.TextCtrl(self,
                                    style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER)
        self.password.SetToolTipString("Your password on OSF "
                                       "(will be checked securely with https)")
        self.fieldsSizer.Add(self.password,
                             pos=(2, 1), flag=wx.ALIGN_LEFT)
        # remember me
        self.fieldsSizer.Add(wx.StaticText(self, label="Remember me"),
                             pos=(3, 0), flag=wx.ALIGN_RIGHT)
        self.rememberMe = wx.CheckBox(self, True)
        self.rememberMe.SetToolTipString("We won't store your password - "
                                         "just an authorisation token")
        self.fieldsSizer.Add(self.rememberMe,
                             pos=(3, 1), flag=wx.ALIGN_LEFT)

        # buttons (Log in, Cancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cancelBtn = wx.Button(
            self, wx.ID_CANCEL, 'Cancel')
        self.Bind(wx.EVT_BUTTON, self.onCancel, id=wx.ID_CANCEL)
        btnSizer.Add(self.cancelBtn, wx.ALIGN_RIGHT)

        self.okBtn = wx.Button(self, wx.ID_OK, "Login")
        self.okBtn.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.onLogin, id=wx.ID_OK)
        btnSizer.Add(self.okBtn, wx.ALIGN_RIGHT)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(self.fieldsSizer, 0, wx.ALL, 5)
        self.main_sizer.Add(btnSizer, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        self.SetSizerAndFit(self.main_sizer)

    def onLogin(self, event):
        """
        Check credentials and login
        """
        if not havePyosf:
            dialogs.MessageDialog(parent=self.parent, type='Warning', title="pyosf not found",
                                  message='You need pyosf to log in to Open Science Framework',
                                  )
            return None
        username = self.username.GetValue()
        pword = self.password.GetValue()
        rememberMe = bool(self.rememberMe.GetValue())
        try:
            session = pyosf.Session(username=username,
                                    password=pword, remember_me=rememberMe)
            self.app.osf_session = session
            self.updateStatus("Successful authentication", color=(0, 255, 0))
            time.sleep(0.5)
            self.Destroy()
        except pyosf.AuthError:
            self.updateStatus("Failed to Authenticate. Check username/password", color=(255, 0, 0))

    def onCancel(self, event):
        self.Destroy()

    def updateStatus(self, status, color=(0,0,0)):
        self.status.SetLabelText("Failed to Authenticate. Check username/password")
        self.status.SetForegroundColour(color) # set text color
        self.main_sizer.Fit(self)


class SearchDlg(wx.Dialog):
    defaultStyle = (wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT |
                    wx.TAB_TRAVERSAL | wx.RESIZE_BORDER)

    def __init__(self, app, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=defaultStyle):
        title = "Search OSF (Open Science Framework)"
        wx.Dialog.__init__(self, None, -1, title, pos, size, style)
        self.app = app

        # to show detail of current selection
        self.detailsPanel = DetailsPanel(parent=self)

        # create list of my projects (no search?)
        self.myProjectsPanel = ProjectsPanel(self, self.detailsPanel)
        self.updateUserProjs()  # update the info in myProjectsPanel

        # create list of searchable public projects
        self.publicProjectsPanel = ProjectsPanel(self, self.detailsPanel)
        self.publicProjectsPanel.setContents('')


        # sizers: on the left we have search boxes
        leftSizer = wx.BoxSizer(wx.VERTICAL)
        leftSizer.Add(wx.StaticText(self, -1, "My Projects"),
                      flag=wx.EXPAND | wx.ALL, border=5)
        leftSizer.Add(self.myProjectsPanel,
                      proportion=1,
                      flag=wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT,
                      border=10)
        searchSizer = wx.BoxSizer(wx.HORIZONTAL)
        searchSizer.Add(wx.StaticText(self, -1, "Search Public:"))
        self.searchTextCtrl = wx.TextCtrl(self, -1, "")
        leftSizer.Add(searchSizer)
        tagsSizer = wx.BoxSizer(wx.HORIZONTAL)
        tagsSizer.Add(wx.StaticText(self, -1, "Tags:"))
        self.tagsTextCtrl = wx.TextCtrl(self, -1, "psychopy")
        leftSizer.Add(tagsSizer)
        leftSizer.Add(self.publicProjectsPanel,
                      proportion=1,
                      flag=wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT,
                      border=10)

        # sizers: on the right we have detail
        rightSizer = wx.BoxSizer(wx.VERTICAL)
        rightSizer.Add(wx.StaticText(self, -1, "Project Info"),
                       flag=wx.EXPAND | wx.ALL,
                       border=5)
        rightSizer.Add(self.detailsPanel,
                       proportion=1,
                       flag=wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT,
                       border=10)

        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mainSizer.Add(leftSizer, flag=wx.EXPAND, proportion=1, border=5)
        self.mainSizer.Add(rightSizer, flag=wx.EXPAND, proportion=1, border=5)
        self.SetSizerAndFit(self.mainSizer)

        aTable = wx.AcceleratorTable([(0,  wx.WXK_ESCAPE, wx.ID_CANCEL),
                                      ])
        self.SetAcceleratorTable(aTable)

    def updateUserProjs(self):
        if self.app.osf_session.user_id is None:
            self.myProjectsPanel.setContents(
                "No user logged in. \n\n"
                "Go to menu item Projects>Users>")
        else:
            myProjs = self.app.osf_session.find_user_projects()
            self.myProjectsPanel.setContents(myProjs)


class ProjectsPanel(scrolledpanel.ScrolledPanel):
    """A scrollable panel showing a list of projects. To be used within the
    Project Search dialog
    """
    def __init__(self, parent, detailsPanel):
        scrolledpanel.ScrolledPanel.__init__(self, parent, -1, size=(450, 200),
                                        style=wx.SUNKEN_BORDER, name="Mine")
        self.parent = parent
        self.knownProjects = {}
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.mainSizer)  # don't do Fit
        self.mainSizer.Fit(self)

        self.SetAutoLayout(True)
        self.SetupScrolling()

    def setContents(self, projects):
        self.project = projects
        self.DestroyChildren()  # start with a clean slate

        if type(projects) in [str, unicode]:
            # just text for a window so display
            self.mainSizer.Add(
                wx.StaticText(self, -1, projects),
                flag=wx.EXPAND | wx.ALL, border=5,
                )
        else:
            # a list of projects
            self.projView = dataview.DataViewListCtrl(self)

            # Give it some columns.
            # The ID col we'll customize a bit:
            self.projView.AppendTextColumn('id', width=100)
            self.projView.AppendTextColumn('title', width=450)
            for thisProj in projects:
                self.knownProjects[thisProj.id] = thisProj
                self.projView.AppendItem([thisProj.id, thisProj.title])
            self.mainSizer.Add(self.projView, flag=wx.EXPAND | wx.ALL, border=5,)
            self.Bind(dataview.EVT_DATAVIEW_SELECTION_CHANGED,
                      self.onChangeSelection)

        self.FitInside()

    def onChangeSelection(self, event):
        # update the SearchDlg.detailsPanel with new project
        row = self.projView.GetSelectedRow()
        projID = self.projView.GetTextValue(row=row, col=0)
        proj = self.knownProjects[projID]
        self.parent.detailsPanel.setProject(proj)

class DetailsPanel(richtext.RichTextCtrl):
    def __init__(self, parent, style=wx.VSCROLL|wx.NO_BORDER):
        richtext.RichTextCtrl.__init__(self, parent, -1, style=style)
        self.parent = parent

        self.urlStyle = rt.TextAttrEx()
        self.urlStyle.SetTextColour(wx.BLUE)
        self.urlStyle.SetFontUnderlined(True)
        self.rtc.Bind(wx.EVT_TEXT_URL, self.OnURL)

        self.h1 = rt.TextAttrEx()
        self.h1.SetFontSize(18)
        self.h1.SetFontBold(True)

    def setProject(self, project):
        self.Clear()

        if project is None:
            return  # we're done

        self.BeginStyle(self.h1)
        self.WriteText(project.title)
        self.EndStyle()

        self.Newline()
        self.BeginStyle(self.urlStyle)
        self.BeginURL(url="https://osf.io/{}".format(project.id))
        self.WriteText("https://osf.io/{}".format(project.id))
        self.EndURL()
        self.EndStyle()

        self.Newline()
        self.Newline()

        self.WriteText(project.attributes['description'])

    def OnURL(self, evt):
        wx.MessageBox(evt.GetString(), "URL Clicked")

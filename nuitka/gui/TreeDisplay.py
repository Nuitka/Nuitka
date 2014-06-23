#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" Module with functions to display a node tree.

Useful to getting an idea of what the internal representation of Nuitka is about a source
code.
"""

import sys

from PyQt4 import QtCore, QtGui, uic

from nuitka import SourceCodeReferences, Utils


# The API requires a signature, sometimes we don't use it, pylint: disable=R0201
# Also using private stuff from classes, probably ok, pylint: disable=W0212

class NodeTreeModelItem:
    def __init__(self, node, parent = None):
        self.parent_treeitem = parent
        self.node = node

        self.children = None

    def appendChild(self, _item):
        assert False

    def _children(self):
        if self.children is None:
            self.children = [
                NodeTreeModelItem( child, self )
                for child in
                self.node.getVisitableNodes()
            ]

        if self.node.isPythonModule():
            self.children.extend(
                NodeTreeModelItem( child, self )
                for child in
                self.node.getFunctions()
            )


        return self.children

    def child(self, row):
        return self._children()[ row ]

    def childCount(self):
        return len( self._children() )

    def columnCount(self):
        return 2

    def data(self, column):
        if column == 0:
            result = self.node.getDescription()
        elif column == 1:
            result = self.node.getDetail()
        else:
            assert False

        return QtCore.QVariant( result )

    def parent(self):
        return self.parent_treeitem

    def row(self):
        return self.parent_treeitem._children().index( self ) if self.parent else 0

class NodeTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, root, parent = None):
        QtCore.QAbstractItemModel.__init__( self, parent )

        self.root_node = root
        self.root_item = NodeTreeModelItem( root )

    def columnCount(self, _parent):
        return self.root_item.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()

        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        item = index.internalPointer()

        return QtCore.QVariant( item.data( index.column() ) )

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if section == 0:
                return QtCore.QVariant( "Node Type" )
            elif section == 1:
                return QtCore.QVariant( "Node Detail" )

            return self.root_item.data( section )

        return QtCore.QVariant()

    def index(self, row, column, parent):
        if row < 0 or column < 0 or row >= self.rowCount( parent ) or column >= self.columnCount( parent ):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parent = self.root_item
        else:
            parent = parent.internalPointer()

        child = parent.child( row )

        if child:
            return self.createIndex( row, column, child )
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        child = index.internalPointer()
        parent = child.parent()

        if parent == self.root_item:
            return QtCore.QModelIndex()

        return self.createIndex( parent.row(), 0, parent )

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent = self.root_item
        else:
            parent = parent.internalPointer()

        return parent.childCount()

    def getNodeFromPath(self, tree_path):
        tree_path = list( tree_path )

        current = self.root_node

        while tree_path:
            current = current.getVisitableNodes()[ tree_path[0] ]

            del tree_path[0]

        return current

    def getItemFromSourceRef(self, source_ref):
        def check(item):
            if item.node.getSourceReference() == source_ref:
                return item

            for child in item._children():
                result = check( child )

                if result is not None:
                    return result

        return check( self.root_item )


class InspectNodeTreeDialog(QtGui.QDialog):
    def __init__(self, *args):
        QtGui.QDialog.__init__( self, *args )

        ui_dir = Utils.dirname( __file__ )
        ui_filename = Utils.joinpath( ui_dir, "dialogs", "InspectPythonTree.ui" )

        uic.loadUi( ui_filename, self )

        self.treeview_nodes.setSelectionMode( self.treeview_nodes.SingleSelection )

        self.displayed = None
        self.source_code = None
        self.model = None
        self.moving = None

    def setModel(self, model):
        self.treeview_nodes.setModel( model )
        self.treeview_nodes.expandAll()

    @QtCore.pyqtSignature("on_treeview_nodes_clicked(QModelIndex)")
    def onTreeviewNodesClicked(self, item):
        tree_path = []

        while item.isValid():
            tree_path.insert( 0, item.row() )

            item = item.parent()

        clicked_node = self.model.getNodeFromPath( tree_path )
        source_ref = clicked_node.getSourceReference()

        self.moving = True

        self.textedit_source.moveCursor( 1, 0 )

        for _i in range( 1, source_ref.getLineNumber()  ):
            self.textedit_source.moveCursor( 12, 0 )

        self.textedit_source.setFocus()

        self.moving = False

    @QtCore.pyqtSignature( "on_textedit_source_cursorPositionChanged()")
    def onTexteditSourceCursorMoved(self):
        if self.moving:
            return

        pos = self.textedit_source.textCursor().position()

        code = self.source_code[:pos]

        line = 1

        for char in code:
            if char == "\n":
                line += 1

        # print "Line", line

        item = self.model.getItemFromSourceRef(
            self.displayed.atLineNumber(
                line = line
            )
        )

        if item is not None:
            item_path = []

            while item:
                item_path.insert( 0, item )

                item = item.parent()

            index = QtCore.QModelIndex()

            parent = self.model.root_item

            for item in item_path[1:]:
                index = index.child( parent._children().index( item )+1, 1 )
                parent = item

            # print self.treeview_nodes.visualRect( index )

    def loadSource(self, filename):
        self.moving = True
        self.source_code = open( filename ).read()
        self.textedit_source.setPlainText( self.source_code  )
        self.moving = False

        self.displayed = SourceCodeReferences.fromFilename(
            filename    = filename,
            future_spec = None
        )


def displayTreeInspector(tree):
    app = QtGui.QApplication( sys.argv )

    model = NodeTreeModel( tree )

    dialog = InspectNodeTreeDialog()
    dialog.setModel( model )
    dialog.model = model

    from . import SyntaxHighlighting

    SyntaxHighlighting.addPythonHighlighter(
        document = dialog.textedit_source.document()
    )
    dialog.loadSource( tree.getFilename() )

    dialog.setWindowFlags( QtCore.Qt.Window )
    dialog.show()

    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app.exec_()

# 
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
# 
#     Part of "Nuitka", my attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
# 
#     If you submit patches to this software in either form, you automatically
#     grant me a copyright assignment to the code, or in the alternative a BSD
#     license to the code, should your jurisdiction prevent this. This is to
#     reserve my ability to re-license the code at any time.
# 
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 

import sys

try:
    from PyQt4 import QtCore, QtGui, uic

    class NodeTreeModelItem:
        def __init__( self, node, parent = None ):
            self.parent_treeitem = parent
            self.node = node

            self.children = None

        def appendChild( self, item ):
            raise NotImplemented

        def _children( self ):
            if self.children is None:
                self.children = [ NodeTreeModelItem( child, self ) for child in self.node.getVisitableNodes() ]

            return self.children

        def child( self, row ):
            return self._children()[ row ]

        def childCount( self ):
            return len( self._children() )

        def columnCount( self ):
            return 2

        def data( self, column ):
            if column == 0:
                result = self.node.getDescription()
            elif column == 1:
                result = self.node.getDetail()
            else:
                assert False

            return QtCore.QVariant( result )

        def parent( self ):
            return self.parent_treeitem

        def row( self ):
            return self.parent_treeitem._children().index( self ) if self.parent else 0

    class NodeTreeModel( QtCore.QAbstractItemModel ):
        def __init__( self, root, parent = None ):
            QtCore.QAbstractItemModel.__init__( self, parent )

            self.root_node = root
            self.root_item = NodeTreeModelItem( root )

        def columnCount( self, parent ):
            return self.root_item.columnCount()

        def data( self, index, role ):
            if not index.isValid():
                return QtCore.QVariant()

            if role != QtCore.Qt.DisplayRole:
                return QtCore.QVariant()

            item = index.internalPointer()

            return QtCore.QVariant( item.data( index.column() ) )

        def flags( self, index ):
            if not index.isValid():
                return QtCore.Qt.ItemIsEnabled

            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

        def headerData( self, section, orientation, role ):
            if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
                if section == 0:
                    return QtCore.QVariant( "Node Type" )
                elif section == 1:
                    return QtCore.QVariant( "Node Detail" )

                return self.root_item.data( section )

            return QtCore.QVariant()

        def index( self, row, column, parent ):
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

        def parent( self, index ):
            if not index.isValid():
                return QtCore.QModelIndex()

            child = index.internalPointer()
            parent = child.parent()

            if parent == self.root_item:
                return QtCore.QModelIndex()

            return self.createIndex( parent.row(), 0, parent )

        def rowCount( self, parent ):
            if parent.column() > 0:
                return 0

            if not parent.isValid():
                parent = self.root_item
            else:
                parent = parent.internalPointer()

            return parent.childCount()

    class InspectNodeTreeDialog( QtGui.QDialog ):
        def __init__( self, *args ):
            QtGui.QWidget.__init__( self, *args )
            uic.loadUi( "dialogs/InspectPythonTree.ui", self )

        def setModel( self, model ):
            self.treeview_nodes.setModel( model )
            self.treeview_nodes.expandAll()


    def displayTreeInspector( tree ):
        app = QtGui.QApplication( sys.argv )

        model = NodeTreeModel( tree )

        dialog = InspectNodeTreeDialog()
        dialog.setModel( model )
        dialog.show()

        app.exec_()

except ImportError:
    pass



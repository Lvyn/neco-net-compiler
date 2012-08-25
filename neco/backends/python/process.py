
from neco.extsnakes import Pid

class SONode(object):
    
    def __init__(self, pid=None):
        self.pid = pid
        self.children = []
        self.active = False

    def copy(self):
        node = SONode(self.pid)
        for child in self.children:
            node.children.append(child.copy())
        node.active = self.active
        return node
    
    def insert_node(self, node):
        index = 0
        for child in self.children:
            if child.pid < node.pid:
                index += 1
            elif child.pid == node.pid:
                return child
            else:
                break
        self.children.insert(index, node)
        return node
    
    def expanded_insert(self, pid):
        node = self
        for frag in pid:
            node = node.insert_node(SONode(Pid.from_list([frag])))
        node.active = True # set leaf as active
        
    def reduce_sibling_offsets(self):
        """
        >>> n = SONode(None)
        >>> n.expanded_insert(Pid.from_str('1.1.1'))
        >>> n.expanded_insert(Pid.from_str('1.2.1'))
        >>> n.expanded_insert(Pid.from_str('1.3.1'))
        >>> n.print_structure()
        <active=F>
        |-1-<active=F>
          |-1-<active=F>
          | |-1-<active=T>
          |-2-<active=F>
          | |-1-<active=T>
          |-3-<active=F>
            |-1-<active=T>
        >>> _ = n.reduce_sibling_offsets()
        >>> n.print_structure()
        <active=F>
        |-1-<active=F>
          |-1-<active=F>
          | |-1-<active=T>
          |-2-<active=F>
          | |-1-<active=T>
          |-3-<active=F>
            |-1-<active=T>
        >>> n = SONode(None)
        >>> n.expanded_insert(Pid.from_str('2.4.7'))
        >>> n.expanded_insert(Pid.from_str('2.5.8'))
        >>> n.expanded_insert(Pid.from_str('2.6.9'))
        >>> _ = n.reduce_sibling_offsets()
        >>> n.print_structure()
        <active=F>
        |-1-<active=F>
          |-1-<active=F>
          | |-1-<active=T>
          |-2-<active=F>
          | |-1-<active=T>
          |-3-<active=F>
            |-1-<active=T>
        >>> n = SONode(None)
        >>> n.expanded_insert(Pid.from_str('2.42.7'))
        >>> n.expanded_insert(Pid.from_str('2.31.8'))
        >>> n.expanded_insert(Pid.from_str('2.32.8'))
        >>> n.expanded_insert(Pid.from_str('22.32.9'))
        >>> _ = n.reduce_sibling_offsets()
        >>> n.print_structure()
        <active=F>
        |-1-<active=F>
        | |-1-<active=F>
        | | |-1-<active=T>
        | |-2-<active=F>
        | | |-1-<active=T>
        | |-4-<active=F>
        |   |-1-<active=T>
        |-3-<active=F>
          |-1-<active=F>
            |-1-<active=T>
        """
        new_pids_map = {}
        self._reduce_sibling_offsets(old_prefix=[], new_prefix=[], new_pids_map=new_pids_map)
        return new_pids_map
    
    def _reduce_sibling_offsets(self, old_prefix, new_prefix, new_pids_map):
        """
        >>> from pprint import pprint
        >>> n = SONode(None)
        >>> n.expanded_insert(Pid.from_str('2.42.7'))
        >>> n.expanded_insert(Pid.from_str('2.31.8'))
        >>> n.expanded_insert(Pid.from_str('2.32.8'))
        >>> n.expanded_insert(Pid.from_str('22.32.9'))
        >>> new_pid_dict = {} 
        >>> n._reduce_sibling_offsets([], [], new_pid_dict)
        >>> n.print_structure()
        <active=F>
        |-1-<active=F>
        | |-1-<active=F>
        | | |-1-<active=T>
        | |-2-<active=F>
        | | |-1-<active=T>
        | |-4-<active=F>
        |   |-1-<active=T>
        |-3-<active=F>
          |-1-<active=F>
            |-1-<active=T>
        >>> pprint(new_pid_dict)
        {Pid.from_str('2'): Pid.from_str('1'),
         Pid.from_str('22'): Pid.from_str('3'),
         Pid.from_str('2.32'): Pid.from_str('1.2'),
         Pid.from_str('2.31'): Pid.from_str('1.1'),
         Pid.from_str('22.32'): Pid.from_str('3.1'),
         Pid.from_str('2.42'): Pid.from_str('1.4'),
         Pid.from_str('2.31.8'): Pid.from_str('1.1.1'),
         Pid.from_str('2.42.7'): Pid.from_str('1.4.1'),
         Pid.from_str('2.32.8'): Pid.from_str('1.2.1'),
         Pid.from_str('22.32.9'): Pid.from_str('3.1.1')}
        
        """
        if not self.children:
            return
        
        child_1 = self.children[0]
        old_frag_1 = int(child_1.pid)
        new_frag = 1
        new_pid = Pid.from_list([new_frag])
        child_1.pid = new_pid
        
        _old_pid = Pid.from_list(old_prefix + [old_frag_1])
        _new_pid = Pid.from_list(new_prefix + [new_frag])
        new_pids_map[_old_pid] = _new_pid
        child_1._reduce_sibling_offsets(old_prefix=old_prefix + [old_frag_1],
                                        new_prefix=new_prefix + [new_frag],
                                        new_pids_map=new_pids_map)
        for child_2 in self.children[1:]:
            old_frag_2 = int(child_2.pid)
            difference = old_frag_2 - old_frag_1
            if difference == 1:
                new_frag += 1
            else:
                new_frag += 2
                
            child_2.pid = Pid.from_list([new_frag])
            
            _old_pid = Pid.from_list(old_prefix + [old_frag_2])
            _new_pid = Pid.from_list(new_prefix + [new_frag])
            new_pids_map[_old_pid] = _new_pid
            child_2._reduce_sibling_offsets(old_prefix=old_prefix + [old_frag_2],
                                            new_prefix=new_prefix + [new_frag],
                                            new_pids_map=new_pids_map)
            
            child_1 = child_2
            old_frag_1 = old_frag_2
    
    def strip(self):
        """
        >>> n = SONode();
        >>> n.expanded_insert(Pid.from_str('1.1.1'))
        >>> n.print_structure()
        <active=F>
        |-1-<active=F>
          |-1-<active=F>
            |-1-<active=T>
        >>> n.strip()
        >>> n.print_structure()
        <active=F>
        |-1.1.1-<active=T>
        
        
        >>> n = SONode();
        >>> n.expanded_insert(Pid.from_str('1.1.1'))
        >>> n.expanded_insert(Pid.from_str('1.2.1'))
        >>> n.strip()
        >>> n.print_structure()
        <active=F>
        |-1.1.1-<active=T>
        |-1.2.1-<active=T>
        
        >>> n = SONode();
        >>> n.expanded_insert(Pid.from_str('1.1.1'))
        >>> n.expanded_insert(Pid.from_str('1.2.1'))
        >>> n.expanded_insert(Pid.from_str('1.1'))
        >>> n.strip()
        >>> n.print_structure()
        <active=F>
        |-1.1-<active=T>
        | |-1-<active=T>
        |-1.2.1-<active=T>
        
        >>> n = SONode();
        >>> n.expanded_insert(Pid.from_str('1.1.1'))
        >>> n.expanded_insert(Pid.from_str('1.2.1'))
        >>> n.expanded_insert(Pid.from_str('1.1'))
        >>> n.expanded_insert(Pid.from_str('1.2.1.1'))
        >>> n.expanded_insert(Pid.from_str('1'))
        >>> n.strip()
        >>> n.print_structure()
        <active=F>
        |-1-<active=T>
          |-1-<active=T>
          | |-1-<active=T>
          |-2.1-<active=T>
            |-1-<active=T>
        """
        to_remove = []
        to_add = []
        for child in self.children:
            # strip grandchildren, etc.
            child.strip()
            # handle child
            if not child.active:
                # child need to be stripped
                fragment = child.pid
                # remove child from node
                to_remove.append(child)
                
                # handle grand children
                for grandchild in child.children:
                    # change grandchild pid
                    grandchild.pid = fragment + grandchild.pid
                to_add.append(child.children)
    
        # remove childs
        for child in to_remove:
            self.children.remove(child)
    
        # insert grandchildren
        for grandchildren in to_add:
            for grandchild in grandchildren:
                node = self.insert_node(grandchild)
                if node != grandchild:
                    raise RuntimeError

    def stripped(self):
        """
        >>> n = SONode()
        >>> n.expanded_insert(Pid.from_str('1.1.1'))
        >>> n.print_structure()
        <active=F>
        |-1-<active=F>
          |-1-<active=F>
            |-1-<active=T>
        >>> n.stripped().print_structure()
        <active=F>
        |-1.1.1-<active=T>
        
        
        >>> n = SONode();
        >>> n.expanded_insert(Pid.from_str('1.1.1'))
        >>> n.expanded_insert(Pid.from_str('1.2.1'))
        >>> n.stripped().print_structure()
        <active=F>
        |-1.1.1-<active=T>
        |-1.2.1-<active=T>
        
        >>> n = SONode();
        >>> n.expanded_insert(Pid.from_str('1.1.1'))
        >>> n.expanded_insert(Pid.from_str('1.2.1'))
        >>> n.expanded_insert(Pid.from_str('1.1'))
        >>> n.stripped().print_structure()
        <active=F>
        |-1.1-<active=T>
        | |-1-<active=T>
        |-1.2.1-<active=T>
        
        >>> n = SONode();
        >>> n.expanded_insert(Pid.from_str('1.1.1'))
        >>> n.expanded_insert(Pid.from_str('1.2.1'))
        >>> n.expanded_insert(Pid.from_str('1.1'))
        >>> n.expanded_insert(Pid.from_str('1.2.1.1'))
        >>> n.expanded_insert(Pid.from_str('1'))
        >>> n.stripped().print_structure()
        <active=F>
        |-1-<active=T>
          |-1-<active=T>
          | |-1-<active=T>
          |-2.1-<active=T>
            |-1-<active=T>
        """
        node = self.copy()
        node.strip()
        return node
    
    def reduce_parent_offset(self):
        """
        >>> 
        """
        for child in self.children:
            if len(child.pid) > 2:
                pid = child.pid
                child.pid = pid.prefix() + pid.suffix()
                
        
    
    def print_structure(self, child_prefix='', prefix=''):
        """
        >>> n = SONode(None)
        >>> n.print_structure()
        <active=F>
        >>> _ = n.expanded_insert(Pid.from_str('1.1.1'))
        >>> n.print_structure()
        <active=F>
        |-1-<active=F>
          |-1-<active=F>
            |-1-<active=T>
        >>> _ = n.expanded_insert(Pid.from_str('1.2'))
        >>> n.print_structure()
        <active=F>
        |-1-<active=F>
          |-1-<active=F>
          | |-1-<active=T>
          |-2-<active=T>
        >>> _ = n.expanded_insert(Pid.from_str('1'))
        >>> n.print_structure()
        <active=F>
        |-1-<active=T>
          |-1-<active=F>
          | |-1-<active=T>
          |-2-<active=T>
        """
        
        print "{}<active={}>".format(child_prefix, 'T' if self.active else 'F')
        length = len(self.children) - 1
        child_prefix = prefix + '|-'
        for i, child in enumerate(self.children): 
            child_prefix = prefix + '|-{}-'.format(child.pid)
            new_prefix = prefix + '| ' if i < length else prefix + '  ' 
            child.print_structure(child_prefix, new_prefix)
    
PidTree = SONode

if __name__ == '__main__':
    import doctest
    doctest.testmod()

#include "neco_succiter.h"
#include <cstdlib>

namespace neco {

    //////////////////////////////////////////////////

    succ_iterator::succ_iterator(const state* state,
				 bdd condition,
				 neco_list_t* list):
	kripke_succ_iterator(condition),
	m_state(state),
	m_list(list),
	m_node(list->begin)
    {
	m_node = m_list->begin;
	for ( ; m_node != NULL; m_node = m_node->next) {
	    //Py_INCREF(m_node->elt);
	}
    }

    //////////////////////////////////////////////////

    succ_iterator::~succ_iterator()
    {
	m_node = m_list->begin;
	for ( ; m_node != NULL; m_node = m_node->next) {
	    //Py_DECREF(m_node->elt);
	}
	// do not delete elements
	neco_list_delete(m_list, NULL /* deletion callback */ );
    }

    //////////////////////////////////////////////////

    void succ_iterator::first()
    {
	m_node = m_list->begin;
    }

    //////////////////////////////////////////////////

    void succ_iterator::next()
    {
	assert(m_node != NULL);
	m_node = m_node->next;
    }

    //////////////////////////////////////////////////

    bool succ_iterator::done() const
    {
	return m_node == NULL;
    }

    //////////////////////////////////////////////////

    spot::state* succ_iterator::current_state() const
    {
	neco::state* st = new neco::state( reinterpret_cast<struct Marking*>(m_node->elt) );
	return st;
    }

    //////////////////////////////////////////////////

}

//////////////////////////////////////////////////
// EOF
//////////////////////////////////////////////////

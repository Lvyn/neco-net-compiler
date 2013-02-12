#include "neco_succiter.h"
#include "debug.h"
#include <cstdlib>

namespace neco {

    //////////////////////////////////////////////////

    succ_iterator::succ_iterator(const state* state,
                                 bdd condition,
                                 neco_list_t* list)
            : kripke_succ_iterator(condition)
            , m_state(state)
            , m_list(list)
            , m_node_index(0)
    {
    }

    //////////////////////////////////////////////////

    succ_iterator::~succ_iterator()
    {
        // do not delete elements
        neco_list_delete_elts(m_list, 0 /* deletion callback */ );
    }

    //////////////////////////////////////////////////

    void succ_iterator::first()
    {
        NECO_DEBUG_TRACE("succ_iterator::first");
        m_node_index = 0;
    }

    //////////////////////////////////////////////////

    void succ_iterator::next()
    {
        NECO_DEBUG_TRACE("succ_iterator::next");
        ++m_node_index;
    }

    //////////////////////////////////////////////////

    bool succ_iterator::done() const
    {
        NECO_DEBUG_TRACE("succ_iterator::done");
        return m_list->size() <= m_node_index;
    }

    //////////////////////////////////////////////////

    spot::state* succ_iterator::current_state() const
    {
        NECO_DEBUG_TRACE("succ_iterator::current_state");
        void* elt = (*m_list)[m_node_index];
        assert(elt);
        return new neco::state( static_cast<struct Marking*>(elt) );
    }

    //////////////////////////////////////////////////

}

//////////////////////////////////////////////////
// EOF
//////////////////////////////////////////////////

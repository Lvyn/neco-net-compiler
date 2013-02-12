#include "neco_state.h"
#include "debug.h"

namespace neco {

    //////////////////////////////////////////////////

    state::state(const struct Marking* marking)
            : m_marking(marking)
    {
        Py_INCREF(marking);
    }

    //////////////////////////////////////////////////

    state::~state()
    {
        Py_DECREF(m_marking);
    }

    //////////////////////////////////////////////////


    int state::compare(const spot::state* other) const
    {
        NECO_DEBUG_TRACE("state::compare");
        const state* st = dynamic_cast<const state*>(other);
        assert(st);
        return Model::instance().marking_compare(get_marking(), st->get_marking());
    }

    //////////////////////////////////////////////////

    size_t state::hash() const
    {
        NECO_DEBUG_TRACE("state::hash");
        return Model::instance().marking_hash(get_marking());
    }

    //////////////////////////////////////////////////

    spot::state* state::clone() const
    {
        NECO_DEBUG_TRACE("state::clone");
        return new state( Model::instance().marking_copy(get_marking()) );
    }

    //////////////////////////////////////////////////
}

//////////////////////////////////////////////////
// EOF
//////////////////////////////////////////////////

#include "debug.h"
#include "neco_tgba.h"
#include "neco_state.h"
#include "neco_succiter.h"
#include <spot/ltlast/constant.hh>
#include <cstdio>

namespace neco {

    //////////////////////////////////////////////////

    tgba::tgba(const spot::ltl::atomic_prop_set* sap,
               spot::bdd_dict* dict,
               const spot::ltl::formula* dead)
            : m_dict(dict)
    {
        NECO_DEBUG_TRACE("tgba");
        assert(sap);
        assert(dict);

        size_t s = sap->size();
        m_name.reserve(s);
        m_bddvar.reserve(s);
        m_necovar.reserve(s);

        spot::ltl::atomic_prop_set::iterator it;
        for(it = sap->begin(); it != sap->end(); ++it) {
            if (*it == dead)
                continue;

            int id = -1; /* neco atomic proposition identifier */
            const std::string& name = (*it)->name(); /* atomic proposition name, ex. "p 42" */

            m_name.push_back(name);
            sscanf(name.c_str(), "p %d", &id); /* extract neco proposition identifier */

            if (id == -1) {
                std::cerr << "!E! Invalid atomic proposition " << name.c_str() << std::endl;
                exit(-1);
            }

            m_bddvar.push_back(m_dict->register_proposition(*it, this)); // variable in BDD
            m_necovar.push_back(id); // variable in neco
        }

        if (dead == spot::ltl::constant::false_instance()) {
            m_alive_prop = bddtrue;
            m_dead_prop = bddfalse;

        } else if (dead == spot::ltl::constant::true_instance()) {
            m_alive_prop = bddtrue;
            m_dead_prop = bddtrue;

        } else {
            int var = m_dict->register_proposition(dead, this);
            m_dead_prop = bdd_ithvar(var);
            m_alive_prop = bdd_nithvar(var);
        }
    }

    //////////////////////////////////////////////////

    tgba::~tgba()
    {
        m_dict->unregister_all_my_variables(this);
    }

    //////////////////////////////////////////////////

    const tgba& tgba::operator=(const tgba& other)
    {
        assert(false);
    }

    //////////////////////////////////////////////////

    tgba::tgba(const tgba& other)
    {
        assert(false);
    }

    //////////////////////////////////////////////////

    spot::state* tgba::get_init_state() const {
        NECO_DEBUG_TRACE("get_init_state");
        const struct Marking* m = Model::instance().initial_marking();
        return new neco::state(m);
    }

    //////////////////////////////////////////////////

    spot::tgba_succ_iterator* tgba::succ_iter(const spot::state* local_state,
                                              const spot::state*,
                                              const spot::tgba*) const
    {
        NECO_DEBUG_TRACE("succ_iter");
        static struct NecoCtx null_ctx;

        const neco::state* st = dynamic_cast<const neco::state*>(local_state);
        assert(st);
        bdd cond = state_condition(st);

        neco_list_t* list = Model::instance().succs(st->get_marking(), &null_ctx);
        if (list->size() == 0) {
            cond &= m_dead_prop;
            // Add a self-loop.
            list->push_back( const_cast<struct Marking*>(st->get_marking()) );
        } else {
            cond &= m_alive_prop;
        }
        return new neco::succ_iterator(st, cond, list);
    }

    //////////////////////////////////////////////////

    spot::bdd_dict* tgba::get_dict() const
    {
        NECO_DEBUG_TRACE("get_dict");
        return m_dict;
    }

    //////////////////////////////////////////////////

    std::string tgba::format_state(const spot::state* state) const
    {
        NECO_DEBUG_TRACE("format_state");
        const neco::state* st = dynamic_cast<const neco::state*>(state);
        assert(st);
        return std::string( Model::instance().marking_dump(st->get_marking()));
    }

    //////////////////////////////////////////////////

    bdd tgba::state_condition(const spot::state* state) const
    {
        NECO_DEBUG_TRACE("state_condition");
        const neco::state* st = dynamic_cast<const neco::state*>(state);
        assert(st);

        bdd res = bddtrue;
        size_t varcount = m_name.size();

        for (size_t var = 0; var < varcount; ++var) {
            if (Model::instance().check( st->get_marking(), m_necovar[var] /* atom */ )) {
                res &= bdd_ithvar(m_bddvar[var]);
            } else {
                res &= bdd_nithvar(m_bddvar[var]);
            }
        }
        return res;
    }

    //////////////////////////////////////////////////

}

//////////////////////////////////////////////////
// EOF
//////////////////////////////////////////////////

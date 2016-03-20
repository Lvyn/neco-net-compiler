#ifndef _NECO_TGBA_H_
#define _NECO_TGBA_H_

#include "neco_model.h"
#include <bddx.h>
#include <vector>
#include <spot/twa/bdddict.hh>
#include <spot/kripke/kripke.hh>
#include <spot/tl/apcollect.hh>

namespace neco
{

//! Class representing a tgba containing neco states.
class tgba final
    : public spot::kripke
{
public:
                                            tgba(const spot::atomic_prop_set* sap,
                                                 spot::bdd_dict_ptr dict,
                                                 spot::formula dead);

	virtual                                 ~tgba();

	virtual spot::state*                    get_init_state() const override;
	virtual spot::twa_succ_iterator*       succ_iter(const spot::state* local_state) const override;

                                            //! Get the condition of a \a state.
	virtual bdd                             state_condition(const spot::state* state) const override;


	virtual std::string                     format_state(const spot::state* state) const;

private:
                                                tgba(const tgba& other) = delete;
        const tgba&                             operator=(const tgba& other) = delete;

private:
	std::vector<std::string>                m_name;         //!< names of atomic propositions
	std::vector<int>                        m_bddvar;	    //!< associated BDD variables
	std::vector<int>                        m_necovar;	    //!< associated neco model variables, ie., atomic propositions IDs.
	bdd                                     m_alive_prop;   //!< value of alive proposition
	bdd                                     m_dead_prop;    //!< value of dead proposition
};

}

#endif /* _NECO_TGBA_H_ */

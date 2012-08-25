#ifndef _NECO_TGBA_H_
#define _NECO_TGBA_H_

#include "neco_model.h"
#include <bdd.h>
#include <vector>
#include <spot/tgba/bdddict.hh>
#include <spot/kripke/kripke.hh>
#include <spot/tgba/state.hh>
#include <spot/ltlvisit/apcollect.hh>

namespace neco
{

    //! Class representing a tgba with neco states.
    class tgba: public spot::kripke
    {
    public:
	//! Constructor
	tgba(const spot::ltl::atomic_prop_set* sap,
	     spot::bdd_dict* dict,
	     const spot::ltl::formula* dead);

	//! Destructor
	virtual ~tgba();

	//! Initial state of the tgba.
	virtual spot::state* get_init_state() const;

	//! Get a successor iterator of a \a local state.
	virtual spot::tgba_succ_iterator* succ_iter(const spot::state* local_state,
						    const spot::state*,
						    const spot::tgba*) const;

	//! Get the bdd_dict used by the tgba.
	virtual spot::bdd_dict* get_dict() const;

	//! Get a string representation of a \a state.
	virtual std::string format_state(const spot::state* state) const;

	//! Get the condition of a \a state.
	virtual bdd state_condition(const spot::state* state) const;

    private:
	//! Copy constructor, disabled: non copyable
	tgba(const tgba& other);
	//! Assignment operator, disabled: non copyable
	const tgba& operator=(const tgba& other);

    private:
	spot::bdd_dict* m_dict;          //!< bdd dict used by the tgba
	std::vector<std::string> m_name; //!< names of atomic propositions
	std::vector<int> m_bddvar;	 //!< associated BDD variables
	std::vector<int> m_necovar;	 //!< associated neco model variables, ie., atomic propositions IDs.
	bdd m_alive_prop;                //!< value of alive proposition
	bdd m_dead_prop;                 //!< value of dead proposition
    };

}

#endif /* _NECO_TGBA_H_ */

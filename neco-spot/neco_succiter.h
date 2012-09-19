#ifndef _NECO_SUCCITER_H_
#define _NECO_SUCCITER_H_

#include "neco_model.h"
#include "neco_state.h"

#include <spot/kripke/kripke.hh>
#include <spot/tgba/state.hh>
#include <bdd.h>

#include "ctypes.h"

namespace neco {

    class state;

    //! Successor states iterator.
    //!
    //! This iterator enumerates successor states of a state,
    //! modes of Petri net transitions are not stored.
    class succ_iterator: public spot::kripke_succ_iterator
    {
    public:
	//! Constructor.
	//!
	//! \param state current state in the tgba.
	//! \param condition is the one returned bu current_condition().
	//! \param list list of successor markings, states will be build on the fly.
	succ_iterator(const state* state, bdd condition,
		      neco_list_t* list);

	//! Destructor.
	virtual ~succ_iterator();

	//! Set the iterator at the beginning.
 	virtual void first();

	//! Advance by one.
	virtual void next();

	//! All enumerated ?
	virtual bool done() const;

	//! Get the current state.
	virtual spot::state* current_state() const;

    private:
	//! Copy constructor, disabled: non copyable.
	succ_iterator(const succ_iterator& other);

	//! Assignment operator, disabled: non copyable.
	const succ_iterator& operator=(const succ_iterator& other);

    private:
	const state* m_state;     //!< current state.
	neco_list_t* m_list;      //!< list of successor markings.
	neco_list_node_t* m_node; //!< current node, used for iteration over the list.
    };
}

#endif /* _NECO_SUCCITER_H_ */

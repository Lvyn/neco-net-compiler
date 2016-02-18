#ifndef _NECO_SUCCITER_H_
#define _NECO_SUCCITER_H_

#include "neco_model.h"
#include "neco_state.h"

#include <spot/kripke/kripke.hh>
#include <bddx.h>

#include "ctypes.h"

namespace neco {

class state;

//! Successor states iterator.
//!
//! This iterator enumerates successor states of a state,
//! modes of Petri net transitions are not stored.
class succ_iterator final
    : public spot::kripke_succ_iterator
{
public:
                                //! Constructor.
                                //!
				//! \param state current state in the tgba.
				//! \param condition is the one returned bu current_condition().
				//! \param list list of successor markings, states will be build on the fly.
                                succ_iterator(const state* current_state_tgba,
                                              bdd current_condition,
                                              neco_list_t* successor_list);
	virtual                     ~succ_iterator();

				//! Set the iterator at the beginning.
	virtual bool                first() override;
                                //! Advance by one.
	virtual bool                next() override;
                                //! All enumerated ?
	virtual	bool                done() const override;

				//! Get the current state.
	virtual spot::state*        dst() const override;

private:
				    succ_iterator(const succ_iterator& other) = delete;
	const succ_iterator&        operator=(const succ_iterator& other) = delete;

private:
	const state*                m_state;        //!< current state.
	neco_list_t*                m_list;         //!< list of successor markings.
	int                         m_node_index;   //!< current node, used for iteration over the list.
};

} /* namespace neco */

#endif /* _NECO_SUCCITER_H_ */

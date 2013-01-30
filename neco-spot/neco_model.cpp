#include "neco_model.h"
#include <cassert>
#include <iostream>

namespace neco {

    //////////////////////////////////////////////////

    Model::Model()
    {
        if (import_net() != 0 ) {
            PyErr_Print();
        }
        if (import_checker() != 0) {
            PyErr_Print();
        }
    }

    //////////////////////////////////////////////////

    Model::Model(const Model& other)
    {
        assert(false && "noncopyable");
    }

    //////////////////////////////////////////////////

    Model::~Model()
    {
    }

    //////////////////////////////////////////////////

    const Model& Model::operator=(const Model& other)
    {
        assert(false && "noncopyable");
    }

    //////////////////////////////////////////////////

    const struct Marking* Model::initial_marking() const
    {
        neco_init();
    }

    //////////////////////////////////////////////////

    neco_list_t* Model::succs(const struct Marking* m) const
    {
        return neco_succs(const_cast<struct Marking*>(m));
    }

    //////////////////////////////////////////////////

    int Model::marking_hash(const struct Marking* m) const
    {
        return neco_marking_hash(const_cast<struct Marking*>(m));
    }

    //////////////////////////////////////////////////

    int Model::marking_compare(const struct Marking* m1, const struct Marking* m2) const
    {
        return neco_marking_compare(const_cast<struct Marking*>(m1), const_cast<struct Marking*>(m2));
    }

    //////////////////////////////////////////////////

    const struct Marking* Model::marking_copy(const struct Marking* m) const
    {
        return const_cast<const struct Marking*>(neco_marking_copy(const_cast<struct Marking*>(m)));
    }

    //////////////////////////////////////////////////

    char* Model::marking_dump(const struct Marking* m) const
    {
        return neco_marking_dump(const_cast<struct Marking*>(m));
    }

    //////////////////////////////////////////////////

    int Model::check(const struct Marking* m, int atom) const
    {
        int val = neco_check(const_cast<struct Marking*>(m), atom);
        return val;
    }

    //////////////////////////////////////////////////

} // ns neco

#include "neco_model.h"
#include "debug.h"
#include <cassert>
#include <iostream>

namespace neco {

    //////////////////////////////////////////////////

    Model::Model()
    {
        NECO_DEBUG_TRACE("Model::Model");
        std::cout << "importing net" << std::endl;
        if (import_net() != 0 ) {
            PyErr_Print();
        }

        std::cout << "importing checker" << std::endl;
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
        NECO_DEBUG_TRACE("Model::Model~");
    }

    //////////////////////////////////////////////////

    const Model& Model::operator=(const Model& other)
    {
        assert(false && "noncopyable");
    }

    //////////////////////////////////////////////////

    const struct Marking* Model::initial_marking() const
    {
        NECO_DEBUG_TRACE("Model::initial_marking");
        return neco_init();
    }

    //////////////////////////////////////////////////

    struct NecoCtx* Model::initial_ctx() const
    {
        NECO_DEBUG_TRACE("Model::initial_ctx");
        struct Marking* m = neco_init();
        return neco_ctx(m);
    }

    //////////////////////////////////////////////////

    neco_list_t* Model::succs(const struct Marking* m, struct NecoCtx* ctx) const
    {
        NECO_DEBUG_TRACE("Model::succs");
        return neco_succs(const_cast<struct Marking*>(m), ctx);
    }

    //////////////////////////////////////////////////

    int Model::marking_hash(const struct Marking* m) const
    {
        NECO_DEBUG_TRACE("Model::marking_hash");
        return neco_marking_hash(const_cast<struct Marking*>(m));
    }

    //////////////////////////////////////////////////

    int Model::marking_compare(const struct Marking* m1, const struct Marking* m2) const
    {
        NECO_DEBUG_TRACE("Model::marking_compare");
        return neco_marking_compare(const_cast<struct Marking*>(m1), const_cast<struct Marking*>(m2));
    }

    //////////////////////////////////////////////////

    const struct Marking* Model::marking_copy(const struct Marking* m) const
    {
        NECO_DEBUG_TRACE("Model::marking_copy");
        return const_cast<const struct Marking*>(neco_marking_copy(const_cast<struct Marking*>(m)));
    }

    //////////////////////////////////////////////////

    char* Model::marking_dump(const struct Marking* m) const
    {
        NECO_DEBUG_TRACE("Model::marking_dump");
        return neco_marking_dump(const_cast<struct Marking*>(m));
    }

    //////////////////////////////////////////////////

    int Model::check(const struct Marking* m, int atom) const
    {
        NECO_DEBUG_TRACE("Model::check");
        return neco_check(const_cast<struct Marking*>(m), atom);
    }

    //////////////////////////////////////////////////

} // ns neco

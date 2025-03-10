#include "app.h"

int xyz = 389;
const char* name = "William";

int g() {
  return xyz+1;
}

EXPORTED_SYMBOL
PyObject* pynone_a() {
  // printf("in 'a.dylib' -- PyNone = %p\n", PyNone);
  return PyNone;
}

EXPORTED_SYMBOL
PyObject* pysome_a() { return PySomething; }


typedef int (*FUN_PTR)(int);
extern FUN_PTR pointer_to_add10();

EXPORTED_SYMBOL
int add10(int a) {
  FUN_PTR f = pointer_to_add10();
  return (*f)(a);
}



int add20(const int a) { return a + 20; }

typedef int (*FUN_PTR)(int);

EXPORTED_SYMBOL
FUN_PTR pointer_to_add20() { return &add20; }

extern FUN_PTR pointer_to_add389();

EXPORTED_SYMBOL
int add389(int a) {
  FUN_PTR f = pointer_to_add389();
  return (*f)(a);
}


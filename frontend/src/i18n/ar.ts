export const ar = {
    logout: "تسجيل الخروج",
    email: "حساب الإلكتروني",
    password: "كلمة المرور",
    username: "اسم",
    first_name: "الاسم الأول",
    last_name: "اسم العائلة",
    phone: "رقم الهاتف",
    continue: "التالي",
    name: "اسم",
    description: "الوصف",
    whole_price: "سعر الجملة",
    retail_price: "سعر المفرق",
    confirmPassword: "اعد كتابة كلمة المرور",
    back: "عودة",
    welcome: "مرحباً يا",
    submit: "تسجيل",
    search: "بحث",
    notes:"ملاحظات",
    inputErrorMessages: {
        emailRequiredMessage: "لم تدخل حسابك",
        emailPatternMessage: "لم تدخل حساباً صحيحاً",
        passwordRequiredMessage: "لم تدخل كلمة المرور",
        passwordWeakMessage: "كلمة المرور ضعيفة.",
        passwordMediumMessage: "كلمة المرور متوسطة.",
        passwordMismatchMessage: "كلمتا المرور غير متطابقتين.",
        usernameMinMessage: "يجب ان يكون بطول ثلاثة أحرف على الاقل",
        usernameRequiredMessage: "لم تدخل اسمك",
        firstNameRequiredMessage: "لم تدخل الاسم الأول",
        firstNameMinMessage: "يجب أن يكون الاسم الأول حرفين على الأقل",
        lastNameRequiredMessage: "لم تدخل اسم العائلة",
        lastNameMinMessage: "يجب أن يكون اسم العائلة حرفين على الأقل",
    },
    login: {
        title: "تسجيل دخول",
        subtitle: "قم بإدخال حسابك و كلمة المرور",

        serverErrorMessages: {
            400: "كلمة السر أو الحساب غير صحيحان",
            500: "خطأ في المخدم"
        },
        register: "ليس لديك حساب ؟",
        registerLink: "أنشئ واحداً"
    },
    register: {
        step1: {
            businessTitle: "إنشاء حساب عمل",
            title: "إنشاء حساب",
            subtitle: "ادخل اسمك و حسابك الإلكتروني",
            login: "لديك حساب ؟",
            loginLink: "سجل دخولك",
            tos: "من خلال انشاءك لحساب فأنت توافق على",
            tosLink: "شروط الخدمة",
            dpa: "و",
            dpaLink: "اتفاقيات معالجة البيانات",
            registerBusiness: "تريد إدارة عملك ؟",
            registerBusinessLink: "أنشىء حساب عمل",
        },
        step2: {
            subtitle: "ادخل كلمة المرور"
        }
    },
    Products: "بضائع",
    Supplier: "موردون",
    categories: "أصناف",
    items: "العناصر",
    bills: "الفواتير",
    purchaseBills:"فواتير مشتريات",
    noNotes:"لا يوجد ملاحظات",
    Suppliers: {
        newSuppliers: "إضافة مورد جديد",
        addSupplier: "أضف المورد",
        deleteTitle: "حذف مورد",
        deleteConfirm: "هل أنت متأكد أنك تريد حذف هذا المورد؟",
        confirm: "تأكيد",
        cancel: "إلغاء"
    },
    SuppliersMessages: {
        nameRequired: "اسم المورد مطلوب.",
        phoneRequired: "رقم الهاتف مطلوب.",
        phoneMin: "رقم الهاتف غير صالح.",
        serverError: "حدث خطأ أثناء إضافة المورد.",
        createSuccess: "تمت إضافة مورد جديد",
        updateSuccess: "تم تحديث المورد بنجاح",
        editSuccess: "تم تحديث المورد بنجاح",
        deleteSuccess: "تم حذف المورد بنجاح",
        successMessage: "تمت إضافة مورد جديد"
    },
    InventoryCategories: {
        newCategory: "إضافة فئة جديدة",
        addCategory: "أضف الفئة",
        deleteTitle: "حذف فئة",
        deleteConfirm: "هل أنت متأكد أنك تريد حذف هذه الفئة؟"
    },
    InventoryCategoriesMessages: {
        serverError: "حدث خطأ أثناء معالجة الفئة.",
        createSuccess: "تمت إضافة فئة جديدة",
        updateSuccess: "تم تحديث الفئة بنجاح",
        deleteSuccess: "تم حذف الفئة بنجاح"
    },
    InventoryBills: {
        newBill: "إضافة فاتورة جديدة",
        addBill: "أضف الفاتورة",
        deleteTitle: "حذف فاتورة",
        deleteConfirm: "هل أنت متأكد أنك تريد حذف هذه الفاتورة؟",
        createEditNotImplemented: "إنشاء/تعديل خطوط الفاتورة غير منفذ بعد"
    },
    InventoryBillsMessages: {
        serverError: "حدث خطأ أثناء معالجة الفاتورة.",
        createSuccess: "تمت إضافة فاتورة جديدة",
        updateSuccess: "تم تحديث الفاتورة بنجاح",
        deleteSuccess: "تم حذف الفاتورة بنجاح"
    },
    supplier: "المورد",
    manager: "المدير",
    date: "التاريخ",
    inventory: "مستودع",
    Orders: "طلبات",
    finance: "مالية",
    id: "معرف",
    none: "غير محدد",
    actions:"أفعال",
    details: "تفاصيل",
    products: {
        serverErrorMessages: {
            500: "خطأ في المخدم"
        },
        newProduct: "إضافة منتج جديد",
        addProduct: "أضف المنتج",
        productNameRequired: "اسم المنتج مطلوب.",
        retailPriceRequired: "سعر البيع مطلوب.",
        retailPriceMin: "لا يمكن أن يكون سعر البيع سالبًا.",
        wholePriceRequired: "سعر الجملة مطلوب.",
        wholePriceMin: "لا يمكن أن يكون سعر الجملة سالبًا.",
        serverError: "حدث خطأ أثناء إضافة المنتج.",
        deleteTitle: "حذف منتج",
        deleteConfirm: "هل أنت متأكد أنك تريد حذف هذا المنتج؟",
        createSuccess: "تمت إضافة منتج جديد",
        updateSuccess: "تم تحديث المنتج بنجاح",
        deleteSuccess: "تم حذف المنتج بنجاح",
        successMessage: "تمت إضافة منتج جديد"
    },
    tableFilter: {
        addFilter: "إضافة فلتر",
        removeAll: "إزالة الكل",
        column: "العمود",
        value: "القيمة",
        min: "الحد الأدنى",
        max: "الحد الأقصى"
    },
    tableSettings: {
        groupBy: "تجميع حسب",
        displayColumns: "عرض الأعمدة"
    },
    supplierDetails:"تفاصيل المورد :"
    ,
    item: "عنصر",
    category: "فئة",
    quantity: "الكمية",
    unit_price: "سعر الوحدة",
    discount: "الخصم",
    expiry_date: "تاريخ الانتهاء",
    guest: "زائر",
    // Header labels for `location.state.location`, rendered by appLayout via
    // `t(...)`. A key that is missing here renders the raw English identifier.
    inventory_bills: "الفواتير",
    billDetails: "تفاصيل الفاتورة :",
    categoryDetails: "تفاصيل الفئة :",
    itemsCount: "عدد العناصر",
    InventoryBillLines: {
        newLine: "إضافة سطر جديد",
        addLine: "أضف السطر",
        editLine: "تعديل السطر",
        deleteTitle: "حذف سطر",
        deleteConfirm: "هل أنت متأكد أنك تريد حذف هذا السطر؟",
        billMissing: "لم يتم تحديد فاتورة."
    },
    InventoryBillLinesMessages: {
        serverError: "حدث خطأ أثناء معالجة السطر.",
        createSuccess: "تمت إضافة سطر جديد",
        updateSuccess: "تم تحديث السطر بنجاح",
        deleteSuccess: "تم حذف السطر بنجاح",
        itemRequired: "العنصر مطلوب.",
        categoryRequired: "الفئة مطلوبة.",
        quantityRequired: "الكمية مطلوبة.",
        quantityMin: "يجب أن تكون الكمية أكبر من صفر.",
        priceMin: "لا يمكن أن يكون السعر سالبًا."
    },
    
}
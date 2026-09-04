import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import { useNavigate } from "react-router"
import ControlledInput from "../../../../components/ControlledInput"
import Form from "../../../../components/Form"
import Text from "../../../../components/Text"
import Button from "../../../../components/Button"
import { useBoundStore } from "../../../../store/useBoundStore"
import { HugeiconsIcon } from "@hugeicons/react"
import { ViewIcon, ViewOffSlashIcon } from "@hugeicons/core-free-icons"
import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { register } from "../../services/auth.service"
import { setAuthHeader } from "../../../../services/api"
import type { RegisterFieldsValues } from "../../types/authForms"
import { decodeAccessToken } from "../../utility/decodeAccessToken"

const getPasswordStrength = (password: string) => {
    if (password.length < 8) return "weak"

    const hasLowercase = /[a-z]/.test(password)
    const hasUppercase = /[A-Z]/.test(password)
    const hasNumber = /\d/.test(password)
    const hasSymbol = /[^A-Za-z0-9]/.test(password)

    const score = Number(hasLowercase) + Number(hasUppercase) + Number(hasNumber) + Number(hasSymbol)

    if (score >= 4 && hasLowercase && hasUppercase && hasNumber && hasSymbol) return "strong"
    if ((hasLowercase && hasUppercase && hasNumber) || (hasLowercase && hasNumber && hasSymbol) || (hasUppercase && hasNumber && hasSymbol)) return "medium"

    return "weak"
}

export const Step2 = () => {
    const [isVisable, setisVisable] = useState(true)
    const setAuthenticated = useBoundStore(state => state.authSlice.actions.setIsAuthenticated)
    const resetRegisterformData = useBoundStore(state => state.authSlice.actions.resetRegisterformData)

    const setIsGuest = useBoundStore(state => state.authSlice.actions.setIsGuest)
    const setUser = useBoundStore(state => state.authSlice.actions.setUser)
    const registerformData = useBoundStore(state => state.authSlice.registerformData)
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { control, handleSubmit, getValues,setError,formState:{errors}} = useForm<RegisterFieldsValues>({
        defaultValues: {
            password: "",
            confirmPassword: ""
        },
        mode: "all"
    })
    const { mutate, isPending } = useMutation({
        mutationKey: ["auth", "register"],
        mutationFn: register
    })
    const onSubmit = (data: RegisterFieldsValues) => {
        if (isPending) return
        //@ts-ignore
        mutate({...registerformData,password:data.password ,password2:data.confirmPassword , is_verified:true}, {
            onError: () => {
                setError("root.server", { type: "server", message: t("login.serverErrorMessages.400") })
            },
            onSuccess: (data) => {
                const accessPayload = decodeAccessToken(data.access)
                if (accessPayload) {
                    setAuthHeader(data.access)
                    setIsGuest(false)
                    setAuthenticated(true)
                    setUser({ id: accessPayload.user_id, role: accessPayload.role, email: accessPayload.email, username: "" ,first_name:accessPayload.first_name,last_name:accessPayload.last_name})
                    resetRegisterformData()
                    if (accessPayload.role === "CUSTOMER")
                        navigate("/store/")
                    else
                        // was: navigate("/app/inventory/bills", { state: { location: "inventory/bills" } })
                        navigate("/app/supplier/bills", { state: { location: "supplierBills" } })
                    
                }
            }
        })
    }


    return (
        <Form className="w-2xs" onSubmit={handleSubmit(onSubmit)}
         ServerError={errors.root?.server}
            Buttons={
                <div className="*:mb-8">
                    <div className="flex gap-x-8">
                        <Button className="w-full mt-4">{t("submit")}</Button>
                        <Button type="button" onClick={() => { navigate("..") }} variants="secondary" className="w-full mt-4">{t("back")}</Button>
                    </div>
                    
                </div>
            }
        >
            <div className="flex flex-col items-center mb-8 *:mb-4">
                <Text size="20" weight="bold">{t("register.step1.title")}</Text>
                <Text size="16" weight="medium" muted>{t('register.step1.subtitle')}</Text>
            </div>
            <ControlledInput<RegisterFieldsValues>
                name="password"
                autoComplete="off"
                control={control}
                state="normal"
                type={isVisable ? "text" : "password"}
                buttonIcon={<HugeiconsIcon size={22} icon={isVisable ? ViewOffSlashIcon : ViewIcon} />}
                onClick={() => { setisVisable(!isVisable) }}
                rules={
                    {
                        required: { message: t('inputErrorMessages.passwordRequiredMessage'), value: true },
                        validate: {
                            checkPassword: (value) => {
                                const strength = getPasswordStrength(String(value))

                                if (strength === "weak") {
                                    return t('inputErrorMessages.passwordWeakMessage')
                                }

                                if (strength === "medium") {
                                    return t('inputErrorMessages.passwordMediumMessage')
                                }

                                return true
                            }
                        }
                    }
                }

            />
            <ControlledInput<RegisterFieldsValues>
                name="confirmPassword"
                autoComplete="off"
                control={control}
                state="normal"
                type="password"
                rules={
                    {
                        required: { message: t('inputErrorMessages.passwordRequiredMessage'), value: true },
                        validate: {
                            checkConfirmPassword: (value) => {
                                if (getValues("password") !== value) {
                                    return t('inputErrorMessages.passwordMismatchMessage')
                                }

                                return true
                            }
                        }
                    }
                }
            />
        </Form>
    )
}

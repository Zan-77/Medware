import { useForm } from "react-hook-form"
import { useMutation } from "@tanstack/react-query"
import { login } from "../services/auth.service"
import { useTranslation } from 'react-i18next';
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";
import { setAuthHeader } from "../../../services/api";
import { decodeAccessToken } from "../utility/decodeAccessToken";
import ControlledInput from "../../../components/ControlledInput"
import Text from "../../../components/Text"
import Form from "../../../components/Form";
import Button from "../../../components/Button";
import { useBoundStore } from "../../../store/useBoundStore";
import { HugeiconsIcon } from "@hugeicons/react"
import { ViewIcon, ViewOffSlashIcon } from "@hugeicons/core-free-icons"
import type { LoginFieldsValues } from "../types/authForms";


export const LoginPage = () => {
    const [isVisable, setIsVisable] = useState(true)

    const navigate = useNavigate()
    const setIsAuthenticated = useBoundStore(state => state.authSlice.actions.setIsAuthenticated)
    const setIsGuest = useBoundStore(state => state.authSlice.actions.setIsGuest)
    const setUser = useBoundStore(state => state.authSlice.actions.setUser)
    const { t } = useTranslation()
    const { mutate, isPending } = useMutation({
        mutationKey: ["auth", "login"],
        mutationFn: login
    })
    const { control, handleSubmit, setError, clearErrors, formState: { errors }, watch } = useForm<LoginFieldsValues>({
        defaultValues: {
            email: "",
            password: ""
        },
        mode: "all"
    })
    const [email, password] = watch(["email", "password"])
    useEffect(() => {
        clearErrors("root.server")
    }, [email, password])

    const onSubmit = (data: LoginFieldsValues) => {
        if (isPending) return
        mutate(data, {
            onError: () => {
                setError("root.server", { type: "server", message: t("login.serverErrorMessages.400") })
            },
            onSuccess: (data) => {
                const accessPayload = decodeAccessToken(data.access)
                if (accessPayload) {
                    setAuthHeader(data.access)
                    setIsGuest(false)
                    setIsAuthenticated(true)
                    setUser({ id: accessPayload.user_id, role: accessPayload.role, email: accessPayload.email, username: "", first_name: accessPayload.first_name, last_name: accessPayload.last_name })
                    if (accessPayload.role === "CUSTOMER" || accessPayload.role === "GUEST")
                        navigate("/store/")
                    else
                        navigate("/app/products", { state: { location: "Products" } })

                }
            }
        })
    }

    return (
        <Form className="w-2xs" onSubmit={handleSubmit(onSubmit)}
            ServerError={errors.root?.server}
            Buttons={
                <div className="*:mb-8">
                    <Button disabled={isPending} className="w-full mt-4">{t("submit")}</Button>
                    <div className="*:mx-px text-center">
                        <Text muted={true}>{t('login.register')}</Text>
                        <Link to="/app/auth/register">{t('login.registerLink')}</Link>
                    </div>
                </div>
            }
        >
            <div className="flex flex-col items-center mb-8 *:mb-4">
                <Text size="20" weight="bold">{t("login.title")}</Text>
                <Text size="16" weight="medium" muted>{t('login.subtitle')}</Text>
            </div>
            <div className="*:mb-2">
                <ControlledInput<LoginFieldsValues>
                    name="email"
                    control={control}
                    state="normal"
                    rules={{ required: { message: t('inputErrorMessages.emailRequiredMessage'), value: true } }}
                />
                <ControlledInput<LoginFieldsValues>
                    name="password"
                    control={control}
                    state="normal"
                    type={isVisable ? "text" : "password"}
                    rules={{ required: { message: t('inputErrorMessages.passwordRequiredMessage'), value: true } }}
                    buttonIcon={<HugeiconsIcon size={22} icon={isVisable ? ViewOffSlashIcon : ViewIcon} />}
                    onClick={() => { setIsVisable(!isVisable) }}
                />
            </div>
        </Form>
    )
}
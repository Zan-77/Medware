import { useForm } from "react-hook-form"
import { useMutation } from "@tanstack/react-query"
import { login } from "../services/auth.service"
import { useTranslation } from 'react-i18next';
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { setAuthHeader } from "../../../services/api";
import { decodeAccessToken } from "../utility/decodeAccessToken";
import ControlledInput from "../../../components/ControlledInput"
import Text from "../../../components/Text"
import Form from "../../../components/Form";
import Button from "../../../components/Button";
import { useBoundStore } from "../../../useBoundStore";
import { HugeiconsIcon } from "@hugeicons/react"
import { ViewIcon, ViewOffSlashIcon } from "@hugeicons/core-free-icons"
import type { Roles } from "../types/roles";
type RegisterFieldValues = {
  email: string
  password: string
  confirmPassword: string
  username: string
  role: Roles
}


export const RegisterPage = () => {
  const [isVisable, setisVisable] = useState(true)
  const [isBusiness, setIsBusiness] = useState(false)
  const [step2, setStep2] = useState(false)
  const navigate = useNavigate()
  const setAuthenticated = useBoundStore(state => state.authSlice.actions.setIsAuthenticated)
  const setIsGuest = useBoundStore(state => state.authSlice.actions.setIsGuest)
  const setUser = useBoundStore(state => state.authSlice.actions.setUser)
  const { t } = useTranslation()
  const { mutate, isPending } = useMutation({
    mutationKey: ["user"],
    mutationFn: login
  })
  const { control, handleSubmit, setError, clearErrors, trigger, formState: { errors }, watch } = useForm<RegisterFieldValues>({
    defaultValues: {
      email: "",
      password: "",
      confirmPassword: "",
      role:"CUSTOMMER"
    },
    mode: "onChange"
  })
  const [email, password] = watch(["email", "password"])
  useEffect(() => {
    clearErrors("root.server")
  }, [email, password])

  const onSubmit = (data: RegisterFieldValues) => {
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
          setAuthenticated(true)
          setUser({ id: accessPayload.user_id, role: accessPayload.role, email: "", username: "" })
          if (accessPayload.role === "CUSTOMMER" || accessPayload.role === "GUEST")
            navigate("/store")
          else
            navigate("/app")

        }
      }
    })
  }

  return (
    <Form className="w-2xs" onSubmit={handleSubmit(onSubmit)}
      ServerError={errors.root?.server}
      Buttons={
        <div className="*:mb-8">
          
            
              <>
                <div className="flex gap-x-8">
                  <Button disabled={isPending} className="flex-1 mt-4">{t("submit")}</Button>
                  <Button type="button" onClick={() => { setStep2(false) }} variants="secondary" disabled={isPending} className="flex-1 mt-4">{t("back")}</Button>
                </div>

              </> 
              
          
        </div>
      }
    >
      <div className="flex flex-col items-center mb-8 *:mb-4">
        <Text size="20" weight="bold">{t(isBusiness ? "register.step1.businessTitle" : "register.step1.title")}</Text>
        <Text size="16" weight="medium" muted>{t(step2 ? 'register.step2.subtitle' : 'register.step1.subtitle')}</Text>
      </div>
      <div className="*:mb-2">
          <div className={step2?"visible":"hidden"}>

          
          </div>
          <div className={!step2?"visible":"hidden"}>
            
          </div>
      </div>
    </Form>
  )
}
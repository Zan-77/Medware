import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import { Link, useLocation, useNavigate } from "react-router"
import type { Roles } from "../../types/roles"
import ControlledInput from "../../../../components/ControlledInput"
import Form from "../../../../components/Form"
import Text from "../../../../components/Text"
import Button from "../../../../components/Button"
import { useBoundStore } from "../../../../store/useBoundStore"
import { useEffect, useState } from "react"
import { v4 as uuidv4 } from 'uuid';
export interface Step1FieldValues {

  email: string
  role: Roles
  first_name: string
  last_name: string
}


export const Step1 = () => {
  const setRegisterformData = useBoundStore(state => state.authSlice.actions.setRegisterformData)
  const registerformData = useBoundStore(state => state.authSlice.registerformData)
  const { t } = useTranslation()
  const navigate = useNavigate()
  const url = useLocation()
  const { control, handleSubmit, setValue } = useForm<Step1FieldValues>({
    defaultValues: {
      email: "",
      first_name: "",
      last_name: "",
      role: "CUSTOMER"
    },
    mode: "all"
  })
  const [inApp, setInApp] = useState(url.pathname.startsWith("/app"))
  const onSubmit = (data: Step1FieldValues) => {
    setRegisterformData({ password: "", confirmPassword: "", username:uuidv4() , ...data })
    navigate("step2")
  }

  useEffect(() => {
    setInApp(url.pathname.startsWith("/app"))
  }, [url.pathname])

  useEffect(() => {
    setValue("role", inApp ? "MANAGER" : "CUSTOMER")
    setValue("email", registerformData.email)
    setValue("first_name", registerformData.first_name)
    setValue("last_name", registerformData.last_name)
  }, [inApp, registerformData, setValue])

  return (
    <Form className="w-2xs" onSubmit={handleSubmit(onSubmit)}
      Buttons={
        <div className="*:mb-8">
          <Button className="w-full mt-4">{t("continue")}</Button>
          <div className="flex flex-col">
            <div>
              <Text muted={true}>{t("register.step1.tos")}</Text>
              <Link to="/tos">{t("register.step1.tosLink")}</Link>
            </div>
            <div className="text-center">
              <Text muted={true}>{t("register.step1.dpa")}</Text>
              <Link to="/tos">{t("register.step1.dpaLink")}</Link>
            </div>
          </div>
          {!inApp && <div className="*:mx-px text-center">
            <Text muted={true}>{t("register.step1.registerBusiness")}</Text>
            <Link to={inApp ? "/store/auth/register" : "/app/auth/register"}>{t("register.step1.registerBusinessLink")}</Link>
          </div>}
        </div>
      }
    >
      <div className="flex flex-col items-center mb-8 *:mb-4">
        <Text size="20" weight="bold">{t(inApp ? "register.step1.businessTitle" : "register.step1.title")}</Text>
        <Text size="16" weight="medium" muted>{t("register.step1.subtitle")}</Text>
      </div>
      <ControlledInput<Step1FieldValues>
        name="first_name"
        control={control}
        state="normal"
        type="text"
        rules={{
          required: {
            message: t("inputErrorMessages.firstNameRequiredMessage"), value: true
          },
          minLength: { message: t("inputErrorMessages.firstNameMinMessage"), value: 2 }
        }}
      />
      <ControlledInput<Step1FieldValues>
        name="last_name"
        control={control}
        state="normal"
        type="text"
        rules={{
          required: {
            message: t("inputErrorMessages.lastNameRequiredMessage"), value: true
          },
          minLength: { message: t("inputErrorMessages.lastNameMinMessage"), value: 2 }
        }}
      />

      <ControlledInput<Step1FieldValues>
        name="email"
        control={control}
        state="normal"
        type="email"
        rules={{
          required: {
            message: t("inputErrorMessages.emailRequiredMessage"), value: true
          },
          pattern: { message: t("inputErrorMessages.emailPatternMessage"), value: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/ }
        }}
      />
    </Form>
  )
}

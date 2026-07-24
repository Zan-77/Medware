
import { Outlet } from "react-router"
import { useThemeStore } from "./Stores/useThemeStore"




const App = () => {
    const theme = useThemeStore(state => state.theme);
    const setDarkTheme = useThemeStore(state => state.setDarkTheme);
   // const setLightTheme = useThemeStore(state => state.setLightTheme);
    setDarkTheme();
    
    const html = document.documentElement
    html.classList.add(theme)
    

    return <Outlet />
}

export default App
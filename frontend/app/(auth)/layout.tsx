import React from 'react'
import BackgroundImage from "@/public/images/login_wall.svg"
import Image from 'next/image';

const AuthLayout = ({ children }: { children: React.ReactNode }) => {
    return (
      <div className="w-full h-screen flex">
        <div className="w-1/2 h-screen bg-cover bg-center" >
            <Image className='p-4' src={BackgroundImage} alt="authImage" style={{ width: '100%' }}/>
        </div>
        <div className="w-1/2 h-screen ">{children}</div>
      </div>
    );
}

export default AuthLayout
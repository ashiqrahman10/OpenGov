import React from 'react'
import BackgroundImage from "@/public/images/login_wall.svg"
import Logo from "@/public/icons/opengov_logo.svg"
import Image from 'next/image';

const AuthLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="w-full h-screen flex p-5 overflow-hidden">
      <div className=' flex-1 rounded-2xl overflow-hidden'>
        <Image className=' w-full' src={BackgroundImage} alt="authImage" />
      </div>
      <div className=" flex-1">{children}</div>
    </div>
  );
}

export default AuthLayout
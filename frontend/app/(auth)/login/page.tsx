import Image from 'next/image'
import React from 'react'
import GoogleIcon from "@/public/icons/google.svg";
import Logo from "@/public/icons/opengov_logo.svg"
import Link from 'next/link';


const page = () => {
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="bg-white rounded px-8 pt-6 pb-8 mb-4 w-full max-w-md">
        <div className="mb-4 text-center">
          <Image src={Logo} alt="OpenGov" className="mb-10 w-32 mx-auto" width={128} height={32} />
            
          <h2 className="text-4xl font-bold font-gloock">Welcome back</h2>
          <p className="text-gray-600 font-poppins">Enter your email and password to access your account</p>
        </div>
        <form>
          <div className="mb-4 mt-4">
            <label htmlFor="email" className="block text-gray-700 font-bold mb-2">
              Email
            </label>
            <input
              id="email"
              type="email"
              placeholder="Enter your email"
              className=" appearance-none  bg-gray-200 rounded-2xl w-full p-3 text-gray-800 leading-tight focus:outline-none focus:shadow-outline"
            />
          </div>
          <div className="mb-6">
            <label htmlFor="password" className="block text-gray-700 font-bold mb-2">
              Password
            </label>
            <input
              id="password"
              type="password"
              placeholder="Enter your password"
              className="bg-gray-200 rounded-2xl appearance-none  w-full p-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            />
          </div>
          <div className="flex items-center justify-between">
          <div className="form-check">
            <input
              className="form-check-input h-4 w-4 border border-gray-50 rounded-sm cursor-pointer"
              type="checkbox"
              id="remember-me"
            />
            <label className="form-check-label ml-2 text-gray-800" htmlFor="remember-me">
              Remember me
            </label>
          </div>
            <a href="#" className="underline inline-block align-baseline font-bold text-sm text-gray-900 hover:text-gray-950">
              Forgot password
            </a>
          </div>
          <div className="mt-6">
            <button
              type="button"
              className="w-full bg-slate-900 hover:bg-slate-950 text-white font-poppins p-3 rounded-2xl focus:outline-none focus:shadow-outline"
            >
              Sign in
            </button>
          </div>
        </form>
        <div className="flex-col items-center justify-center mt-4">
          <p className="text-gray-600 mt-5 text-center">or </p>
          <center className="mt-5">
            <button className="ml-2 w-full flex items-center justify-center bg-white hover:bg-gray-100 text-gray-800 font-semibold p-3 border border-gray-300 rounded-2xl">
              <Image
                src={GoogleIcon}
                alt="Google Icon"
                className="w-5 h-5 mr-3"
              />
              <p>Continue with Google</p>
            </button>
          </center>
          <div className="mt-5 text-center">
            <Link href="/register" className="text-gray-600">
              Don&apos;t have an account?{" "}
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default page